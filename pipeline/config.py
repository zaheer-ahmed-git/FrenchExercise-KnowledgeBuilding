import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = ROOT_DIR / "lessons" / "staging"
RUNS_DIR = ROOT_DIR / "runs"

load_dotenv(ROOT_DIR / ".env")

WORKFLOWS = {
    "fill_in_blanks": "fill_in_blank_lessons",
    "quiz": "quiz_lessons",
}

# Standard neural voices only: HD / Dragon voices are billed at a higher rate.
VOICE_ROTATION = [
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-FR-VivienneMultilingualNeural",
    "fr-FR-RemyMultilingualNeural",
]

# Slightly slower than default so B1-B2 learners can follow.
DEFAULT_SPEAKING_RATE = "-8%"

AUDIO_FORMAT = "audio-24khz-48kbitrate-mono-mp3"
AUDIO_BITRATE_BPS = 48_000
AUDIO_CONTENT_TYPE = "audio/mpeg"

# A real-time synthesis request is capped at 10 minutes of audio, so long
# scripts are split into chunks well under that limit.
TTS_MAX_CHARS_PER_REQUEST = 3000

WORD_COUNT_MIN = 750
WORD_COUNT_MAX = 1500
DURATION_TARGET_SEC = (6 * 60, 10 * 60)
BLANK_COUNT_RANGE = (10, 15)
LESSONS_PER_RUN_RANGE = (1, 4)


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongo_db_name: str
    speech_key: str
    speech_region: str
    storage_connection_string: str
    storage_container: str
    audio_sas_hours: int


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


def load_settings() -> Settings:
    settings = Settings(
        mongodb_uri=_first_env("MONGODB_URI"),
        mongo_db_name=_first_env("MONGO_DB_NAME", "MONGODB_DB", default="french_learning"),
        speech_key=_first_env("AZURE_SPEECH_KEY"),
        speech_region=_first_env("AZURE_SPEECH_REGION"),
        storage_connection_string=_first_env("AZURE_STORAGE_CONNECTION_STRING"),
        storage_container=_first_env(
            "AZURE_STORAGE_CONTAINER", "AZURE_BLOB_CONTAINER", default="french-lessons"
        ),
        audio_sas_hours=int(_first_env("AUDIO_SAS_HOURS", default="168")),
    )
    missing = [
        name
        for name, value in {
            "MONGODB_URI": settings.mongodb_uri,
            "AZURE_SPEECH_KEY": settings.speech_key,
            "AZURE_SPEECH_REGION": settings.speech_region,
            "AZURE_STORAGE_CONNECTION_STRING": settings.storage_connection_string,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables in .env: {', '.join(missing)}")
    return settings
