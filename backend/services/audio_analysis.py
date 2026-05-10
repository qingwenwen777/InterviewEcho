"""
音频特征提取 - A 负责实现。

入参：临时音频路径 + Whisper 已转写结果（避免重复转写）
出参：VoiceMetrics dict（参见 docs/expression_module_contract.md §2.1）

约定：
- 必须复用 stt_service.transcribe_detailed() 的结果，不重新调 Whisper
- 音频 < 3 秒 或 转写为空 → 返回 None
- 填充词清单从 evaluation.filler_words import，禁止硬编码
- wpm 中文按字/分钟，英文按 1 词≈2 字折算
"""

import re
from typing import Optional

import librosa
import numpy as np

from evaluation.filler_words import FILLER_WORDS

# ============== 常量 ==============
MIN_DURATION_SEC = 3.0      # 短于此时长视为无效输入
PAUSE_THRESHOLD_DB = 30     # librosa.effects.split 的能量门槛（dB）
LONG_PAUSE_SEC = 1.5        # 段间间隔超过此值算一次"长停顿"
SAMPLE_RATE = 16000         # 与 Whisper 原生采样率一致

# 中文字符正则（CJK 统一汉字）
_CJK_RE = re.compile(r'[\u4e00-\u9fff]')
# 英文单词正则
_EN_WORD_RE = re.compile(r'[A-Za-z]+')

# ============== 繁简转换映射（仅覆盖填充词及高频字） ==============
# Whisper 输出字符体系不稳定，同一段音频可能时简时繁，会导致填充词漏数。
# 这里手写一份小型映射表，不依赖 opencc，只覆盖 filler_words.py 涉及的字 + 常见高频字。
_T2S_MAP = {
    # filler_words 相关
    "個": "个", "這": "这", "麼": "么", "後": "后", "實": "实",
    "對": "对", "說": "说",
    # 其他高频
    "為": "为", "時": "时", "間": "间", "現": "现", "場": "场",
    "問": "问", "題": "题", "經": "经", "驗": "验", "識": "识",
    "標": "标", "點": "点", "結": "结", "構": "构", "處": "处",
    "級": "级", "計": "计", "劃": "划", "課": "课", "業": "业",
    "頭": "头", "於": "于", "進": "进", "關": "关", "從": "从",
    "電": "电", "腦": "脑", "網": "网", "頁": "页", "資": "资",
    "據": "据", "庫": "库", "務": "务", "傳": "传", "輸": "输",
    "選": "选", "擇": "择", "響": "响", "應": "应",
    "覽": "览", "誤": "误", "節": "节", "適": "适", "雜": "杂",
    "靜": "静", "蘋": "苹", "態": "态", "圍": "围", "繞": "绕",
    "簡": "简", "體": "体", "繁": "繁", "轉": "转", "換": "换",
    "韓": "韩", "馬": "马", "齊": "齐", "區": "区", "別": "别",
    "歡": "欢", "謝": "谢",
}


def _to_simplified(text: str) -> str:
    """
    简易繁→简转换，仅处理映射表里的单字符。
    用于让 _count_fillers 和 _count_chars 不漏数繁体词
    （如 Whisper 输出 "那個"，需先转 "那个" 才能匹配 FILLER_WORDS）。
    """
    if not text:
        return text
    return text.translate(str.maketrans(_T2S_MAP))


# ============== 内部 helper ==============

def _count_chars(text: str) -> int:
    """
    中文按字算，英文按 1 词≈2 字折算。
    例："Hello HashMap 哈希表" → 2*2 + 3 = 7
    """
    cn = len(_CJK_RE.findall(text))
    en = len(_EN_WORD_RE.findall(text))
    return cn + en * 2


def _load_audio(audio_path: str):
    """加载音频为单声道 16kHz numpy 数组。"""
    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    duration = len(y) / sr if sr > 0 else 0.0
    return y, sr, duration


def _calc_wpm(text: str, duration_sec: float) -> tuple[float, int]:
    """
    语速：字/分钟。
    Returns: (wpm, char_count)
    """
    char_count = _count_chars(text)
    if duration_sec <= 0:
        return 0.0, char_count
    wpm = char_count / duration_sec * 60
    return round(wpm, 2), char_count


def _calc_pauses(y, sr, segments: list, total_duration: float) -> tuple[float, int]:
    """
    pause_ratio: 1 - 非静音时长占比（基于能量门槛）
    long_pause_count: Whisper segments 之间间隔 > LONG_PAUSE_SEC 的数量
    """
    # pause_ratio
    if total_duration <= 0:
        pause_ratio = 0.0
    else:
        try:
            intervals = librosa.effects.split(y, top_db=PAUSE_THRESHOLD_DB)
            voiced_sec = sum((e - s) for s, e in intervals) / sr if sr > 0 else 0.0
            pause_ratio = max(0.0, 1.0 - voiced_sec / total_duration)
        except Exception as e:
            print(f"[audio_analysis] pause_ratio calc failed: {e}")
            pause_ratio = 0.0

    # long_pause_count: 段间 gap
    long_pause_count = 0
    for i in range(1, len(segments)):
        prev_end = segments[i - 1].get("end", 0)
        curr_start = segments[i].get("start", 0)
        gap = curr_start - prev_end
        if gap > LONG_PAUSE_SEC:
            long_pause_count += 1

    return round(pause_ratio, 3), long_pause_count


def _count_fillers(text: str) -> tuple[list, int]:
    """
    在文本里子串计数填充词。
    先把文本转成简体，避免 Whisper 输出繁体导致漏数（如"那個" vs "那个"）。
    Returns: ([{"word": str, "count": int}, ...], total)
    """
    normalized = _to_simplified(text)
    counts = []
    total = 0
    for word in FILLER_WORDS:
        c = normalized.count(word)
        if c > 0:
            counts.append({"word": word, "count": c})
            total += c
    counts.sort(key=lambda x: -x["count"])
    return counts, total


def _calc_pitch(y, sr) -> tuple[float, float]:
    """
    基频均值与标准差（用 librosa.yin）。
    过滤无效值（静音帧的 yin 输出会贴 fmax 边界）。
    """
    try:
        f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
        f0_valid = f0[(f0 > 60) & (f0 < 450) & (~np.isnan(f0))]
        if len(f0_valid) == 0:
            return 0.0, 0.0
        return round(float(np.mean(f0_valid)), 2), round(float(np.std(f0_valid)), 2)
    except Exception as e:
        print(f"[audio_analysis] pitch calc failed: {e}")
        return 0.0, 0.0


def _calc_volume(y) -> tuple[float, float]:
    """RMS 能量均值与标准差。"""
    try:
        rms = librosa.feature.rms(y=y)[0]
        rms_valid = rms[rms > 1e-4]   # 过滤纯静音帧
        if len(rms_valid) == 0:
            return 0.0, 0.0
        return round(float(np.mean(rms_valid)), 4), round(float(np.std(rms_valid)), 4)
    except Exception as e:
        print(f"[audio_analysis] volume calc failed: {e}")
        return 0.0, 0.0


# ============== 主入口 ==============

def analyze_audio(audio_path: str, whisper_result: dict) -> Optional[dict]:
    """
    Args:
        audio_path: 临时音频文件路径
        whisper_result: stt_service.transcribe_detailed() 完整返回

    Returns:
        VoiceMetrics dict（13 字段，见契约 §2.1）
        或 None（音频太短 / 转写为空 / 加载失败）
    """
    # 1. 输入校验
    if not whisper_result:
        return None

    text = (whisper_result.get("text") or "").strip()
    segments = whisper_result.get("segments") or []

    if not text:
        return None

    # 2. 加载音频
    try:
        y, sr, duration = _load_audio(audio_path)
    except Exception as e:
        print(f"[audio_analysis] Failed to load audio {audio_path}: {e}")
        return None

    # 3. 时长校验
    if duration < MIN_DURATION_SEC:
        print(f"[audio_analysis] Audio too short: {duration:.2f}s, skip")
        return None

    # 4. 各维度计算
    wpm, char_count = _calc_wpm(text, duration)
    pause_ratio, long_pause_count = _calc_pauses(y, sr, segments, duration)
    filler_words, filler_total = _count_fillers(text)
    pitch_mean, pitch_std = _calc_pitch(y, sr)
    volume_mean, volume_std = _calc_volume(y)

    # 5. 标准化 segments（只保留 start/end/text，避免 raw_json 太大）
    slim_segments = [
        {
            "start": float(s.get("start", 0)),
            "end": float(s.get("end", 0)),
            "text": s.get("text", ""),
        }
        for s in segments
    ]

    return {
        "duration_sec": round(duration, 2),
        "transcript": text,
        "segments": slim_segments,

        "wpm": wpm,
        "char_count": char_count,

        "pause_ratio": pause_ratio,
        "long_pause_count": long_pause_count,
        "filler_words": filler_words,
        "filler_total": filler_total,

        "pitch_mean": pitch_mean,
        "pitch_std": pitch_std,
        "volume_mean": volume_mean,
        "volume_std": volume_std,
    }
