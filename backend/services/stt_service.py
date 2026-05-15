import base64
import mimetypes
import os
import subprocess
import tempfile
import threading
from typing import Optional

import httpx

from core.config import settings


class STTService:
    _instance = None
    _model = None
    _model_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(STTService, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: Optional[str] = None):
        """Load local Whisper only when explicitly configured."""
        if settings.ASR_PROVIDER.lower() != "whisper":
            print(f"Speech recognition provider: {settings.ASR_PROVIDER}")
            return None

        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

            import torch
            import whisper

            selected_model = model_name or settings.WHISPER_MODEL
            print(f"Loading Whisper model: {selected_model}...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Whisper will run on: {device}")
            download_root = settings.WHISPER_CACHE_DIR or None
            self._model = whisper.load_model(
                selected_model,
                device=device,
                download_root=download_root,
            )
            print(f"Whisper model loaded: {selected_model}")
        return self._model

    def transcribe(self, audio_path: str, mime_type: Optional[str] = None) -> Optional[str]:
        result = self.transcribe_detailed(audio_path, mime_type=mime_type)
        return result.get("text") if result else None

    def transcribe_detailed(self, audio_path: str, mime_type: Optional[str] = None) -> Optional[dict]:
        """Return text plus a Whisper-compatible segment list for expression analysis."""
        if not os.path.exists(audio_path):
            print(f"STT error: audio file not found at {audio_path}")
            return None

        provider = settings.ASR_PROVIDER.lower()
        if provider == "dashscope":
            return self._transcribe_dashscope(audio_path, mime_type=mime_type)
        if provider == "whisper":
            return self._transcribe_whisper(audio_path)

        print(f"STT error: unsupported ASR_PROVIDER={settings.ASR_PROVIDER}")
        return None

    def _transcribe_whisper(self, audio_path: str) -> Optional[dict]:
        try:
            import torch

            if self._model is None:
                self.load_model()

            options = {
                "fp16": torch.cuda.is_available(),
                "language": settings.WHISPER_LANGUAGE or None,
                "verbose": False,
                "word_timestamps": settings.WHISPER_WORD_TIMESTAMPS,
            }
            print(f"Starting local Whisper transcription for: {audio_path}")
            result = self._model.transcribe(audio_path, **options)
            text = (result.get("text") or "").strip()
            segments = result.get("segments", [])
            language = result.get("language", settings.WHISPER_LANGUAGE or "zh")
            print(f"Local Whisper transcription successful: {len(segments)} segments")
            return {"text": text, "segments": segments, "language": language}
        except Exception as e:
            print(f"Whisper transcription error: {type(e).__name__}: {e}")
            return None

    def _transcribe_dashscope(self, audio_path: str, mime_type: Optional[str] = None) -> Optional[dict]:
        api_key = settings.ASR_API_KEY or settings.LLM_API_KEY
        if not api_key:
            print("DashScope ASR error: missing ASR_API_KEY or LLM_API_KEY")
            return None

        prepared_path = audio_path
        prepared_mime = self._normalize_mime_type(mime_type, audio_path)
        cleanup_path = None

        try:
            if settings.ASR_TRANSCODE_AUDIO:
                converted = self._transcode_for_asr(audio_path)
                if converted:
                    prepared_path, prepared_mime = converted
                    cleanup_path = prepared_path

            file_size = os.path.getsize(prepared_path)
            if file_size > settings.ASR_MAX_AUDIO_BYTES:
                print(f"DashScope ASR error: audio too large after preparation: {file_size} bytes")
                return None

            with open(prepared_path, "rb") as audio_file:
                audio_b64 = base64.b64encode(audio_file.read()).decode("utf-8")

            data_url = f"data:{prepared_mime};base64,{audio_b64}"
            payload = {
                "model": settings.ASR_MODEL,
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": [{"text": ""}],
                        },
                        {
                            "role": "user",
                            "content": [{"audio": data_url}],
                        },
                    ]
                },
                "parameters": {
                    "asr_options": {
                        "enable_itn": settings.ASR_ENABLE_ITN,
                    }
                },
            }
            if settings.ASR_LANGUAGE:
                payload["parameters"]["asr_options"]["language"] = settings.ASR_LANGUAGE

            url = settings.ASR_BASE_URL
            print(f"Starting DashScope ASR: model={settings.ASR_MODEL}, bytes={file_size}")
            with httpx.Client(timeout=settings.ASR_TIMEOUT_SECONDS) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            text = self._extract_dashscope_text(data)
            if not text:
                print(f"DashScope ASR returned empty text. response keys={list(data.keys())}")
                return None

            language = self._extract_dashscope_language(data) or settings.ASR_LANGUAGE or settings.WHISPER_LANGUAGE or "zh"
            print(f"DashScope ASR successful: text[:50]={text[:50]}...")
            return {
                "text": text,
                "segments": [],
                "language": language,
                "provider": "dashscope",
                "model": settings.ASR_MODEL,
            }
        except httpx.HTTPStatusError as e:
            body = e.response.text[:500] if e.response is not None else ""
            print(f"DashScope ASR HTTP error: {e.response.status_code if e.response else 'unknown'} {body}")
            return None
        except Exception as e:
            print(f"DashScope ASR error: {type(e).__name__}: {e}")
            return None
        finally:
            if cleanup_path and os.path.exists(cleanup_path):
                try:
                    os.remove(cleanup_path)
                except OSError:
                    pass

    @staticmethod
    def _normalize_mime_type(mime_type: Optional[str], audio_path: str) -> str:
        value = (mime_type or "").split(";")[0].strip().lower()
        if not value:
            value = mimetypes.guess_type(audio_path)[0] or ""
        aliases = {
            "audio/x-wav": "audio/wav",
            "audio/mp3": "audio/mpeg",
            "audio/x-m4a": "audio/mp4",
        }
        return aliases.get(value, value or "audio/webm")

    @staticmethod
    def _transcode_for_asr(audio_path: str) -> Optional[tuple[str, str]]:
        fd, out_path = tempfile.mkstemp(prefix="asr_", suffix=".mp3")
        os.close(fd)
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            audio_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "64k",
            out_path,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return out_path, "audio/mpeg"
        except Exception as e:
            print(f"ASR audio transcode failed, falling back to original file: {type(e).__name__}: {e}")
            try:
                os.remove(out_path)
            except OSError:
                pass
            return None

    @staticmethod
    def _extract_dashscope_text(data: dict) -> str:
        try:
            content = data["choices"][0]["message"].get("content", "")
        except Exception:
            content = None

        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                elif isinstance(item, str):
                    parts.append(item)
            return "".join(parts).strip()

        output = data.get("output") if isinstance(data, dict) else None
        try:
            content = output["choices"][0]["message"]["content"]
            if isinstance(content, list):
                return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()
            if isinstance(content, str):
                return content.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def _extract_dashscope_language(data: dict) -> str:
        try:
            annotations = data["choices"][0]["message"].get("annotations") or []
            for item in annotations:
                if isinstance(item, dict) and item.get("language"):
                    return item["language"]
        except Exception:
            pass
        return ""


stt_service = STTService()
