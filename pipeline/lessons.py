"""Turn agent-written staging JSON into MongoDB lesson documents."""

import json
import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

# Blanks are written inline by the agent as [[answer]] or [[answer|hint]].
BLANK_PATTERN = re.compile(r"\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]")
BLANK_DISPLAY = "______"

DEFAULT_QUIZ_QUESTION = "Quel résumé correspond le mieux à ce que vous avez entendu ?"


def load_staging(staging_dir: Path) -> list[tuple[Path, dict]]:
    files = sorted(p for p in staging_dir.glob("*.json") if not p.name.startswith("_"))
    lessons = []
    for path in files:
        with path.open(encoding="utf-8") as handle:
            lessons.append((path, json.load(handle)))
    return lessons


def slugify(text: str, max_len: int = 40) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "lesson"


def make_lesson_id(title: str, created_at: datetime) -> str:
    return f"{created_at:%Y%m%d}-{slugify(title)}-{uuid.uuid4().hex[:6]}"


def count_words(text: str) -> int:
    return len(re.findall(r"[\wÀ-ÿ'’-]+", text))


def parse_blanks(script_marked: str) -> dict:
    """Derive the spoken script, display passage, structured segments, and answer key."""
    segments: list[dict] = []
    blanks: list[dict] = []
    spoken_parts: list[str] = []
    display_parts: list[str] = []
    cursor = 0

    for match in BLANK_PATTERN.finditer(script_marked):
        text_before = script_marked[cursor : match.start()]
        if text_before:
            segments.append({"type": "text", "value": text_before})
        spoken_parts.append(text_before)
        display_parts.append(text_before)

        index = len(blanks) + 1
        answer = match.group(1).strip()
        hint = (match.group(2) or "").strip() or None
        blanks.append({"index": index, "answer": answer, "acceptedAnswers": [answer], "hint": hint})
        segments.append({"type": "blank", "index": index})
        spoken_parts.append(answer)
        display_parts.append(f"{BLANK_DISPLAY} ({index})")
        cursor = match.end()

    tail = script_marked[cursor:]
    if tail:
        segments.append({"type": "text", "value": tail})
    spoken_parts.append(tail)
    display_parts.append(tail)

    return {
        "scriptFull": "".join(spoken_parts).strip(),
        "passageWithBlanks": "".join(display_parts).strip(),
        "passageSegments": segments,
        "blanks": blanks,
    }


def spoken_script(workflow: str, staged: dict) -> str:
    if workflow == "fill_in_blanks":
        return parse_blanks(staged.get("scriptMarked", ""))["scriptFull"]
    return staged.get("script", "").strip()


def build_document(workflow: str, staged: dict, *, run_id: str, created_at: datetime) -> dict:
    """Build the MongoDB document (without audio fields, which are added after TTS)."""
    doc = {
        "lessonId": make_lesson_id(staged["title"], created_at),
        "runId": run_id,
        "workflow": workflow,
        "status": "pending",
        "title": staged["title"].strip(),
        "titleFr": staged["titleFr"].strip(),
        "difficulty": staged["difficulty"],
        "language": "fr-FR",
        "topicTags": staged.get("topicTags", []),
        "summaryEn": staged.get("summaryEn", "").strip(),
        "glossary": staged.get("glossary", []),
        "sources": staged["sources"],
        "createdAt": created_at,
    }

    if workflow == "fill_in_blanks":
        doc.update(parse_blanks(staged["scriptMarked"]))
    else:
        doc["scriptFull"] = staged["script"].strip()
        doc["question"] = staged.get("question", DEFAULT_QUIZ_QUESTION)
        doc["options"] = [option["text"].strip() for option in staged["options"]]
        doc["correctIndex"] = next(i for i, option in enumerate(staged["options"]) if option.get("isCorrect"))
        doc["optionRationales"] = [option.get("rationale", "") for option in staged["options"]]
        doc["explanation"] = staged.get("explanation", "")

    doc["wordCount"] = count_words(doc["scriptFull"])
    return doc


def shuffle_quiz_options(doc: dict, rng) -> None:
    """Shuffle in place so the correct answer is not always where the agent wrote it."""
    order = list(range(len(doc["options"])))
    rng.shuffle(order)
    doc["options"] = [doc["options"][i] for i in order]
    doc["optionRationales"] = [doc["optionRationales"][i] for i in order]
    doc["correctIndex"] = order.index(doc["correctIndex"])
