import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo-1106")
    LLM_EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    ASR_PROVIDER: str = os.getenv("ASR_PROVIDER", "dashscope")
    ASR_API_KEY: str = os.getenv("ASR_API_KEY", "")
    ASR_BASE_URL: str = os.getenv("ASR_BASE_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation")
    ASR_MODEL: str = os.getenv("ASR_MODEL", "qwen3-asr-flash")
    ASR_LANGUAGE: str = os.getenv("ASR_LANGUAGE", "zh")
    ASR_TIMEOUT_SECONDS: float = float(os.getenv("ASR_TIMEOUT_SECONDS", "35"))
    ASR_ENABLE_ITN: bool = os.getenv("ASR_ENABLE_ITN", "true").lower() in ("1", "true", "yes")
    ASR_TRANSCODE_AUDIO: bool = os.getenv("ASR_TRANSCODE_AUDIO", "true").lower() in ("1", "true", "yes")
    ASR_MAX_AUDIO_BYTES: int = int(os.getenv("ASR_MAX_AUDIO_BYTES", "10485760"))
    VOICE_UPLOAD_DIR: str = os.getenv("VOICE_UPLOAD_DIR", "")

    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL: str = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_TTS_MODEL: str = os.getenv("MIMO_TTS_MODEL", "mimo-v2.5-tts")
    MIMO_TTS_AUDIO_FORMAT: str = os.getenv("MIMO_TTS_AUDIO_FORMAT", "wav")
    MIMO_TTS_TIMEOUT_SECONDS: float = float(os.getenv("MIMO_TTS_TIMEOUT_SECONDS", "60"))

    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_CACHE_DIR: str = os.getenv("WHISPER_CACHE_DIR", "")
    WHISPER_LANGUAGE: str = os.getenv("WHISPER_LANGUAGE", "zh")
    WHISPER_WORD_TIMESTAMPS: bool = os.getenv("WHISPER_WORD_TIMESTAMPS", "false").lower() in ("1", "true", "yes")
    WHISPER_PRELOAD: bool = os.getenv("WHISPER_PRELOAD", "true").lower() in ("1", "true", "yes")

    INTERVIEW_MAX_FOLLOW_UPS_PER_QUESTION: int = int(os.getenv("INTERVIEW_MAX_FOLLOW_UPS_PER_QUESTION", "1"))
    INTERVIEW_SHORT_ROUNDS_MAX_FOLLOW_UPS: int = int(os.getenv("INTERVIEW_SHORT_ROUNDS_MAX_FOLLOW_UPS", "0"))
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASS: str = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD", "root")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "interview_echo")

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    JUDGE0_BASE_URL: str = os.getenv("JUDGE0_BASE_URL", "http://127.0.0.1:2358")
    JUDGE0_TIMEOUT_SECONDS: float = float(os.getenv("JUDGE0_TIMEOUT_SECONDS", "8"))
    JUDGE0_POLL_INTERVAL_SECONDS: float = float(os.getenv("JUDGE0_POLL_INTERVAL_SECONDS", "0.8"))
    JUDGE0_MAX_POLL_ATTEMPTS: int = int(os.getenv("JUDGE0_MAX_POLL_ATTEMPTS", "30"))
    CODE_MAX_SOURCE_LENGTH: int = int(os.getenv("CODE_MAX_SOURCE_LENGTH", "20000"))
    CODE_MAX_TEST_CASES: int = int(os.getenv("CODE_MAX_TEST_CASES", "30"))
    CODE_MAX_CONCURRENT_JUDGE_CASES: int = int(os.getenv("CODE_MAX_CONCURRENT_JUDGE_CASES", "8"))
    CODE_OUTPUT_LIMIT: int = int(os.getenv("CODE_OUTPUT_LIMIT", "4000"))

settings = Settings()

