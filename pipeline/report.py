from datetime import datetime
from pathlib import Path

from pipeline.config import RUNS_DIR


def _fmt_duration(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes}:{secs:02d}"


def _listen_line(doc: dict, container_public: bool) -> str:
    # SAS tokens are credentials, so private-container links are never written to committed reports.
    if container_public:
        return f"[audio]({doc['audio']['url']})"
    return f"`python -m pipeline.manage link --lesson-id {doc['lessonId']}`"


def write_success_report(
    *,
    run_id: str,
    workflow: str,
    collection: str,
    started_at: datetime,
    docs: list[dict],
    warnings: list[str],
    container_public: bool,
) -> Path:
    total_chars = sum(d["audio"]["ttsCharacters"] for d in docs)
    total_bytes = sum(d["audio"]["bytes"] for d in docs)
    lines = [
        f"# Run {run_id}",
        "",
        "- **Status:** SUCCESS",
        f"- **Workflow:** `{workflow}` (collection `{collection}`)",
        f"- **Started:** {started_at:%Y-%m-%d %H:%M} UTC",
        f"- **Lessons published:** {len(docs)}",
        f"- **Azure TTS characters billed (approx.):** {total_chars:,}",
        f"- **Audio stored:** {total_bytes / 1_048_576:.1f} MB",
        f"- **Container public:** {'yes' if container_public else 'no (generate a time-limited listen link per lesson)'}",
        "",
        "## Lessons",
        "",
    ]
    for doc in docs:
        audio = doc["audio"]
        lines += [
            f"### {doc['titleFr']}",
            "",
            f"- English title: {doc['title']}",
            f"- Lesson id: `{doc['lessonId']}` (Mongo `_id` `{doc['_id']}`)",
            f"- Difficulty: {doc['difficulty']} | words: {doc['wordCount']} | duration: {_fmt_duration(audio['durationSec'])}",
            f"- Voice: `{audio['voiceName']}` at rate `{audio['speakingRate']}`",
            f"- Blob: `{audio['blobPath']}`",
            f"- Listen: {_listen_line(doc, container_public)}",
        ]
        if doc["workflow"] == "fill_in_blanks":
            lines.append(f"- Blanks: {len(doc['blanks'])}")
        else:
            lines.append(f"- Quiz correct option: {doc['correctIndex'] + 1} of 4")
        lines.append("- Sources:")
        lines += [f"  - [{s['title']}]({s['url']})" + (f" ({s['origin']})" if s.get("origin") else "") for s in doc["sources"]]
        lines.append("")

    if warnings:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
    return _write(run_id, "\n".join(lines))


def write_failure_report(*, run_id: str, workflow: str, error: str, cleanup_log: list[str]) -> Path:
    lines = [
        f"# Run {run_id}",
        "",
        "- **Status:** FAILED (nothing was left published)",
        f"- **Workflow:** `{workflow}`",
        "",
        "## Error",
        "",
        "```",
        error.strip(),
        "```",
        "",
        "## Cleanup",
        "",
    ]
    lines += [f"- {entry}" for entry in cleanup_log] or ["- Nothing to clean up (failed before publishing)."]
    return _write(f"{run_id}-FAILED", "\n".join(lines) + "\n")


def _write(name: str, content: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path
