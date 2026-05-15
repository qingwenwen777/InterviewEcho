import os
import threading
from typing import Optional

import torch
import whisper

from core.config import settings


class WhisperSTT:
    _instance = None
    _model = None
    _model_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WhisperSTT, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: Optional[str] = None):
        """Load the configured Whisper model into memory once."""
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

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

    def _transcribe_options(self) -> dict:
        return {
            "fp16": torch.cuda.is_available(),
            "language": settings.WHISPER_LANGUAGE or None,
            "verbose": False,
        }

    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe an audio file and return plain text."""
        if self._model is None:
            self.load_model()

        if not os.path.exists(audio_path):
            print(f"Whisper error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Starting transcription for: {audio_path}")
            result = self._model.transcribe(audio_path, **self._transcribe_options())
            text = result.get("text", "").strip()
            print(f"Transcription successful: {text[:50]}...")
            return text
        except Exception as e:
            print(f"Whisper transcription error: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def transcribe_detailed(self, audio_path: str) -> Optional[dict]:
        """Return Whisper text plus segment timestamps for expression analysis."""
        if self._model is None:
            self.load_model()

        if not os.path.exists(audio_path):
            print(f"Whisper error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Starting detailed transcription for: {audio_path}")
            options = self._transcribe_options()
            options["word_timestamps"] = settings.WHISPER_WORD_TIMESTAMPS
            result = self._model.transcribe(audio_path, **options)
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            language = result.get("language", settings.WHISPER_LANGUAGE or "zh")
            print(f"Detailed transcription successful: {len(segments)} segments, text[:50]={text[:50]}...")
            return {
                "text": text,
                "segments": segments,
                "language": language,
            }
        except Exception as e:
            print(f"Whisper detailed transcription error: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return None


stt_service = WhisperSTT()
