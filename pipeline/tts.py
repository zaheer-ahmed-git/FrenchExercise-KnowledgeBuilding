import re
import time
from dataclasses import dataclass
from xml.sax.saxutils import escape

import requests

from pipeline.config import (
    AUDIO_BITRATE_BPS,
    AUDIO_FORMAT,
    DEFAULT_SPEAKING_RATE,
    TTS_MAX_CHARS_PER_REQUEST,
    Settings,
)

MAX_RETRIES = 4


@dataclass
class SynthesisResult:
    audio: bytes
    voice_name: str
    characters: int
    duration_sec: float
    requests_made: int


def _endpoint(settings: Settings) -> str:
    return f"https://{settings.speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"


def list_voices(settings: Settings, locale: str = "fr-FR") -> list[dict]:
    url = f"https://{settings.speech_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": settings.speech_key}, timeout=30)
    response.raise_for_status()
    return [voice for voice in response.json() if voice.get("Locale") == locale]


def split_into_chunks(script: str, max_chars: int = TTS_MAX_CHARS_PER_REQUEST) -> list[list[str]]:
    """Group paragraphs into chunks under max_chars; oversized paragraphs are split on sentences."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    pieces: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            pieces.append(paragraph)
            continue
        sentences = re.split(r"(?<=[.!?…])\s+", paragraph)
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > max_chars:
                pieces.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            pieces.append(current)

    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    current_len = 0
    for piece in pieces:
        if current_chunk and current_len + len(piece) > max_chars:
            chunks.append(current_chunk)
            current_chunk, current_len = [], 0
        current_chunk.append(piece)
        current_len += len(piece)
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def build_ssml(paragraphs: list[str], voice_name: str, rate: str) -> str:
    body = '<break time="700ms"/>'.join(f"<p>{escape(p)}</p>" for p in paragraphs)
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fr-FR">'
        f'<voice name="{voice_name}"><prosody rate="{rate}">{body}</prosody></voice></speak>'
    )


def _post_ssml(settings: Settings, ssml: str) -> bytes:
    headers = {
        "Ocp-Apim-Subscription-Key": settings.speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": AUDIO_FORMAT,
        "User-Agent": "french-lesson-pipeline",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.post(_endpoint(settings), headers=headers, data=ssml.encode("utf-8"), timeout=180)
        if response.status_code == 200 and response.content:
            return response.content
        retryable = response.status_code in (429, 500, 502, 503, 504)
        if not retryable or attempt == MAX_RETRIES:
            raise RuntimeError(
                f"Azure TTS failed with HTTP {response.status_code}: {response.text[:300]}"
            )
        retry_after = response.headers.get("Retry-After")
        time.sleep(float(retry_after) if retry_after else 2 ** attempt)
    raise AssertionError("unreachable")


def synthesize(settings: Settings, script: str, voice_name: str, rate: str = DEFAULT_SPEAKING_RATE) -> SynthesisResult:
    """Synthesize a long French script to one MP3 by concatenating per-chunk MP3 streams."""
    chunks = split_into_chunks(script)
    if not chunks:
        raise ValueError("Cannot synthesize an empty script")
    audio_parts = [_post_ssml(settings, build_ssml(chunk, voice_name, rate)) for chunk in chunks]
    audio = b"".join(audio_parts)
    return SynthesisResult(
        audio=audio,
        voice_name=voice_name,
        characters=sum(len(p) for chunk in chunks for p in chunk),
        duration_sec=round(len(audio) * 8 / AUDIO_BITRATE_BPS, 1),
        requests_made=len(chunks),
    )
