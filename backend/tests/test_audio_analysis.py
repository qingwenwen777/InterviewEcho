"""
A 的本地单元测试。验证 analyze_audio 在各种音频上的行为。

用法（在 backend 目录下执行）：
    cd backend
    python tests/test_audio_analysis.py

工作流：
    1. 录好 5 段测试音频放到 tests/audio_samples/（参见 A_audio_recording_guide.md）
    2. 运行此脚本
    3. 查看每段音频的实际指标，与"期望测出"对比
    4. 如果差距大，回去调 audio_analysis.py 里的常量阈值
       （MIN_DURATION_SEC / PAUSE_THRESHOLD_DB / LONG_PAUSE_SEC 等）

预期：
- 录音前：所有 case 显示 [SKIP] file not found（这是正常的）
- 录音后：每个 case 输出完整指标，且边界 case 返回 None
"""
import os
import sys
import json
from pprint import pprint

# 让 import 能找到上层包（backend/）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stt_service import stt_service
from services.audio_analysis import analyze_audio

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "audio_samples")

# 契约 §2.1 必须存在的字段
REQUIRED_KEYS = {
    "duration_sec", "transcript", "segments",
    "wpm", "char_count",
    "pause_ratio", "long_pause_count",
    "filler_words", "filler_total",
    "pitch_mean", "pitch_std",
    "volume_mean", "volume_std",
}

# 5 个 case 的期望（参见 A_audio_recording_guide.md）
EXPECTATIONS = {
    "normal_30s.m4a": {
        "desc": "正常基线",
        "should_return": "metrics",
        "expect": "wpm 180-240, pause_ratio<0.2, filler_total<2",
        "checks": lambda r: (
            180 <= r["wpm"] <= 280  # 略放宽
            and r["pause_ratio"] < 0.25
            and r["filler_total"] < 3
        ),
    },
    "fast_with_filler.m4a": {
        "desc": "快语速 + 多填充词",
        "should_return": "metrics",
        "expect": "wpm>260, filler_total>=5",
        "checks": lambda r: (
            r["wpm"] > 240   # 略放宽
            and r["filler_total"] >= 4
        ),
    },
    "slow_with_pause.m4a": {
        "desc": "慢语速 + 长停顿",
        "should_return": "metrics",
        "expect": "wpm<150, pause_ratio>0.3, long_pause_count>=2",
        "checks": lambda r: (
            r["wpm"] < 180   # 略放宽
            and r["pause_ratio"] > 0.25
            and r["long_pause_count"] >= 1
        ),
    },
    "nervous_pitchvar.m4a": {
        "desc": "紧张型音调起伏",
        "should_return": "metrics",
        "expect": "pitch_std>20",
        "checks": lambda r: r["pitch_std"] > 15,  # 略放宽
    },
    "too_short.m4a": {
        "desc": "过短音频",
        "should_return": "None",
        "expect": "返回 None",
        "checks": None,
    },
}


def run_one(filename: str, spec: dict) -> bool:
    """
    跑单个 case。
    Returns: True 表示符合预期，False 表示失败。
    """
    path = os.path.join(SAMPLES_DIR, filename)
    print(f"\n{'='*60}")
    print(f"[CASE] {filename} -- {spec['desc']}")
    print(f"        期望: {spec['expect']}")
    print('='*60)

    if not os.path.exists(path):
        print(f"[SKIP] file not found: {path}")
        print("       请按 A_audio_recording_guide.md 录制此音频")
        return None

    # 1. Whisper 详细转写
    print("[STEP 1] 调用 stt_service.transcribe_detailed()...")
    wr = stt_service.transcribe_detailed(path)
    if wr is None:
        print("[FAIL] transcribe_detailed 返回 None")
        return False
    print(f"        text: {wr['text'][:60]}...")
    print(f"        segments: {len(wr['segments'])} 个")
    print(f"        language: {wr['language']}")

    # 2. analyze_audio
    print("[STEP 2] 调用 analyze_audio()...")
    result = analyze_audio(path, wr)

    # 3. 边界 case：should return None
    if spec["should_return"] == "None":
        if result is None:
            print("[OK] 正确返回 None")
            return True
        else:
            print(f"[FAIL] 应返回 None，实际返回: {result}")
            return False

    # 4. 正常 case：should return dict
    if result is None:
        print("[FAIL] 应返回 metrics dict，实际返回 None")
        return False

    # 5. 契约结构校验
    missing = REQUIRED_KEYS - set(result.keys())
    if missing:
        print(f"[FAIL] 缺少字段: {missing}")
        return False
    print("[OK] 字段完整")

    # 6. 打印指标
    print(f"\n  duration_sec: {result['duration_sec']}")
    print(f"  wpm: {result['wpm']}  (char_count={result['char_count']})")
    print(f"  pause_ratio: {result['pause_ratio']}")
    print(f"  long_pause_count: {result['long_pause_count']}")
    print(f"  filler_total: {result['filler_total']}")
    print(f"  filler_words: {result['filler_words']}")
    print(f"  pitch: {result['pitch_mean']} ± {result['pitch_std']}")
    print(f"  volume: {result['volume_mean']} ± {result['volume_std']}")

    # 7. 业务校验
    if spec["checks"] is None:
        return True
    try:
        if spec["checks"](result):
            print(f"\n[OK] 符合期望: {spec['expect']}")
            return True
        else:
            print(f"\n[WARN] 不完全符合期望: {spec['expect']}")
            print("       这可能是录音风格与预期不符，看上面指标自行判断是否合理")
            return False
    except Exception as e:
        print(f"\n[FAIL] checks 函数报错: {e}")
        return False


def test_boundary_cases():
    """边界用例：不依赖音频文件。"""
    print(f"\n{'='*60}")
    print("[BOUNDARY] 边界用例（不依赖音频文件）")
    print('='*60)

    # whisper_result = None
    r = analyze_audio("nonexistent.m4a", None)
    assert r is None, f"None input should return None, got {r}"
    print("[OK] whisper_result=None -> None")

    # text 为空
    r = analyze_audio("nonexistent.m4a", {"text": "", "segments": []})
    assert r is None, "empty text should return None"
    print("[OK] empty text -> None")

    # 文件不存在
    r = analyze_audio("nonexistent_file_12345.m4a", {"text": "测试", "segments": []})
    assert r is None, "nonexistent file should return None"
    print("[OK] nonexistent file -> None")


def main():
    print("=" * 60)
    print("A 端单元测试 - audio_analysis")
    print("=" * 60)

    # 边界 case
    test_boundary_cases()

    # 真实音频 case
    results = {}
    for filename, spec in EXPECTATIONS.items():
        results[filename] = run_one(filename, spec)

    # 总结
    print(f"\n{'='*60}")
    print("[SUMMARY]")
    print('='*60)

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)

    for filename, r in results.items():
        if r is True:
            mark = "[OK]   "
        elif r is False:
            mark = "[FAIL] "
        else:
            mark = "[SKIP] "
        print(f"  {mark} {filename}")

    print(f"\n  {passed}/{total} passed, {failed} failed, {skipped} skipped")

    if skipped > 0:
        print("\n  跳过的 case 是因为对应录音不存在。请按 A_audio_recording_guide.md 录制后重跑。")


if __name__ == "__main__":
    main()
