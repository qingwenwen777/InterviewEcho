import base64
import re
from typing import Any

import httpx

from core.config import settings


TTS_VOICES = [
    {"id": "mimo_default", "name": "默认", "language": "auto", "gender": "auto"},
    {"id": "冰糖", "name": "冰糖", "language": "zh", "gender": "female"},
    {"id": "茉莉", "name": "茉莉", "language": "zh", "gender": "female"},
    {"id": "苏打", "name": "苏打", "language": "zh", "gender": "male"},
    {"id": "白桦", "name": "白桦", "language": "zh", "gender": "male"},
    {"id": "Mia", "name": "Mia", "language": "en", "gender": "female"},
    {"id": "Chloe", "name": "Chloe", "language": "en", "gender": "female"},
    {"id": "Milo", "name": "Milo", "language": "en", "gender": "male"},
    {"id": "Dean", "name": "Dean", "language": "en", "gender": "male"},
]

TTS_SPEEDS = {
    "slow": "语速略慢，停顿清晰，让候选人有充分时间理解问题。",
    "normal": "语速自然稳定，节奏接近真实技术面试。",
    "fast": "语速稍快但吐字清楚，保持干练的追问节奏。",
}

TTS_STYLES = {
    "calm": "理性、克制、专业，像一位经验丰富的技术面试官。",
    "warm": "温和、鼓励、耐心，保持专业但不过度热情。",
    "strict": "严谨、直接、有压迫感但礼貌，像高标准终面面试官。",
}

_VOICE_IDS = {item["id"] for item in TTS_VOICES}
_AUDIO_MIME_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "pcm16": "audio/L16",
}


class TTSServiceError(RuntimeError):
    pass


def get_tts_options() -> dict[str, Any]:
    return {
        "voices": TTS_VOICES,
        "speeds": [{"id": key, "name": name} for key, name in [("slow", "慢速"), ("normal", "标准"), ("fast", "稍快")]],
        "styles": [{"id": key, "name": name} for key, name in [("calm", "克制"), ("warm", "温和"), ("strict", "严谨")]],
        "default": {"voice": "mimo_default", "speed": "normal", "style": "calm"},
    }


def _normalize_base_url(value: str) -> str:
    base_url = (value or "https://api.xiaomimimo.com/v1").strip().rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def _clean_speech_text(text: str) -> str:
    value = (text or "").strip()
    value = re.sub(r"```[\s\S]*?```", "这里有一段代码，请结合屏幕内容回答。", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"[*_#>~-]+", "", value)
    value = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:2200]


def _build_instruction(speed: str, style: str) -> str:
    speed_prompt = TTS_SPEEDS.get(speed, TTS_SPEEDS["normal"])
    style_prompt = TTS_STYLES.get(style, TTS_STYLES["calm"])
    return (
        f"请用中文技术面试场景朗读。声音风格：{style_prompt}"
        f"朗读节奏：{speed_prompt}"
        "不要读出 Markdown 符号，遇到项目名、技术词和英文缩写时保持清晰自然。"
    )


async def synthesize_interviewer_audio(text: str, voice: str = "mimo_default", speed: str = "normal", style: str = "calm") -> dict[str, str]:
    if not settings.MIMO_API_KEY:
        raise TTSServiceError("TTS 服务尚未配置 MIMO_API_KEY")

    speech_text = _clean_speech_text(text)
    if not speech_text:
        raise TTSServiceError("没有可朗读的文本")

    voice_id = voice if voice in _VOICE_IDS else "mimo_default"
    audio_format = settings.MIMO_TTS_AUDIO_FORMAT or "wav"
    payload = {
        "model": settings.MIMO_TTS_MODEL,
        "messages": [
            {"role": "user", "content": _build_instruction(speed, style)},
            {"role": "assistant", "content": speech_text},
        ],
        "audio": {
            "format": audio_format,
            "voice": voice_id,
        },
    }

    url = f"{_normalize_base_url(settings.MIMO_BASE_URL)}/chat/completions"
    headers = {
        "api-key": settings.MIMO_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.MIMO_TTS_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:360] if exc.response is not None else str(exc)
        raise TTSServiceError(f"TTS 上游返回异常：{detail}") from exc
    except Exception as exc:
        raise TTSServiceError(f"TTS 合成失败：{type(exc).__name__}") from exc

    message = ((data.get("choices") or [{}])[0].get("message") or {})
    audio = message.get("audio") or {}
    audio_base64 = audio.get("data")
    if not audio_base64:
        raise TTSServiceError("TTS 响应中没有音频数据")

    try:
        base64.b64decode(audio_base64, validate=True)
    except Exception as exc:
        raise TTSServiceError("TTS 响应音频不是有效的 base64") from exc

    return {
        "audio_base64": audio_base64,
        "mime_type": _AUDIO_MIME_TYPES.get(audio_format, "audio/wav"),
        "format": audio_format,
        "voice": voice_id,
    }
