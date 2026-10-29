"""Validation that runs before any paid Azure call, and again on stored documents."""

import re
from dataclasses import dataclass, field

from pipeline.config import BLANK_COUNT_RANGE, LESSONS_PER_RUN_RANGE, WORD_COUNT_MAX, WORD_COUNT_MIN
from pipeline.lessons import BLANK_PATTERN, count_words, parse_blanks

FRENCH_MARKERS = re.compile(r"\b(le|la|les|des|du|une|est|et|que|qui|dans|pour|avec|nous|vous)\b", re.IGNORECASE)


@dataclass
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def _require_text(findings: Findings, where: str, staged: dict, key: str) -> None:
    value = staged.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.error(where, f"'{key}' must be a non-empty string")


def _check_common(findings: Findings, where: str, staged: dict) -> None:
    for key in ("title", "titleFr"):
        _require_text(findings, where, staged, key)

    if staged.get("difficulty") not in ("B1", "B2"):
        findings.error(where, "'difficulty' must be 'B1' or 'B2'")

    sources = staged.get("sources")
    if not isinstance(sources, list) or not sources:
        findings.error(where, "'sources' must list at least one cited source")
    else:
        for i, source in enumerate(sources):
            if not isinstance(source, dict) or not str(source.get("url", "")).startswith(("http://", "https://")):
                findings.error(where, f"sources[{i}] needs an http(s) 'url'")
            elif not source.get("title"):
                findings.error(where, f"sources[{i}] needs a 'title'")

    voice = staged.get("voiceName")
    if voice is not None and (not str(voice).startswith("fr-FR-") or "DragonHD" in str(voice)):
        findings.error(where, "'voiceName' must be a standard fr-FR neural voice (no HD voices)")


def _check_script(findings: Findings, where: str, script: str) -> None:
    words = count_words(script)
    if words < WORD_COUNT_MIN or words > WORD_COUNT_MAX:
        findings.error(
            where,
            f"spoken script has {words} words; expected {WORD_COUNT_MIN}-{WORD_COUNT_MAX} for a 6-10 minute lesson",
        )
    if words and len(FRENCH_MARKERS.findall(script)) / words < 0.08:
        findings.warn(where, "script does not look like natural French prose; double-check the language")


def _check_fill_in_blanks(findings: Findings, where: str, staged: dict) -> None:
    marked = staged.get("scriptMarked")
    if not isinstance(marked, str) or not marked.strip():
        findings.error(where, "'scriptMarked' must contain the script with [[answer]] or [[answer|hint]] markers")
        return

    leftover = BLANK_PATTERN.sub("", marked)
    if "[[" in leftover or "]]" in leftover:
        findings.error(where, "malformed blank marker; use [[answer]] or [[answer|hint]] without nesting")

    blanks = parse_blanks(marked)["blanks"]
    low, high = BLANK_COUNT_RANGE
    if not low <= len(blanks) <= high:
        findings.error(where, f"found {len(blanks)} blanks; expected {low}-{high}")
    for blank in blanks:
        if len(blank["answer"].split()) > 4:
            findings.warn(where, f"blank {blank['index']} answer '{blank['answer']}' is long for listening practice")
    answers = [b["answer"].lower() for b in blanks]
    if len(set(answers)) < len(answers):
        findings.warn(where, "some blank answers repeat; prefer varied vocabulary")

    _check_script(findings, where, parse_blanks(marked)["scriptFull"])


def _check_quiz(findings: Findings, where: str, staged: dict) -> None:
    _require_text(findings, where, staged, "script")
    if isinstance(staged.get("script"), str):
        _check_script(findings, where, staged["script"])

    options = staged.get("options")
    if not isinstance(options, list) or len(options) != 4:
        findings.error(where, "'options' must contain exactly 4 summaries")
        return
    texts = []
    for i, option in enumerate(options):
        if not isinstance(option, dict) or not str(option.get("text", "")).strip():
            findings.error(where, f"options[{i}] needs non-empty 'text'")
            return
        texts.append(option["text"].strip())

    correct = [o for o in options if o.get("isCorrect") is True]
    if len(correct) != 1:
        findings.error(where, f"exactly one option must have isCorrect=true (found {len(correct)})")
    if len({t.lower() for t in texts}) != 4:
        findings.error(where, "the four summaries must be distinct")

    lengths = [count_words(t) for t in texts]
    if min(lengths) and max(lengths) / min(lengths) > 1.5:
        findings.warn(where, f"summary lengths vary a lot {lengths}; the longest option can give the answer away")


def validate_batch(workflow: str, lessons: list[tuple[str, dict]]) -> Findings:
    findings = Findings()
    low, high = LESSONS_PER_RUN_RANGE
    if not low <= len(lessons) <= high:
        findings.error("batch", f"found {len(lessons)} lessons; expected {low}-{high}")
    elif len(lessons) < 3:
        findings.warn("batch", f"only {len(lessons)} lesson(s); normal runs produce 3-4")

    titles = [str(staged.get("title", "")).strip().lower() for _, staged in lessons]
    if len(set(titles)) != len(titles):
        findings.error("batch", "lesson titles must be unique within a run")

    for name, staged in lessons:
        _check_common(findings, name, staged)
        if workflow == "fill_in_blanks":
            _check_fill_in_blanks(findings, name, staged)
        else:
            _check_quiz(findings, name, staged)
    return findings


def verify_stored_document(doc: dict) -> list[str]:
    """Consistency checks on the document as read back from MongoDB."""
    problems = []
    if not doc.get("audio", {}).get("url"):
        problems.append("missing audio url")
    if doc["workflow"] == "fill_in_blanks":
        rebuilt = "".join(
            seg["value"] if seg["type"] == "text" else doc["blanks"][seg["index"] - 1]["answer"]
            for seg in doc["passageSegments"]
        ).strip()
        if rebuilt != doc["scriptFull"]:
            problems.append("passage segments plus answers do not reproduce the spoken script")
        if [b["index"] for b in doc["blanks"]] != list(range(1, len(doc["blanks"]) + 1)):
            problems.append("blank indexes are not sequential")
    else:
        if len(doc.get("options", [])) != 4 or doc.get("correctIndex") not in range(4):
            problems.append("quiz must have 4 options and a correctIndex in 0..3")
    return problems
