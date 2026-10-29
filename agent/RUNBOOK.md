# Lesson Run Runbook (Cursor Agent / Codex)

Follow this when the user asks for a run, for example "Generate 3 quiz lessons" or "Create 4 fill-in-the-blank lessons about agents". All commands are run from the repository root in PowerShell. Use `;` to chain commands.

## 0. Understand the request

- Workflow: `quiz` or `fill_in_blanks` (exactly one per run). If unclear, ask.
- Count: default 3, maximum 4.
- Optional focus topic or time window.

## 1. Environment

```powershell
if (-not (Test-Path .venv)) { python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
.\.venv\Scripts\python.exe -m pipeline.manage check
```

If `check` fails, stop and tell the user which service failed. Never print, log, or edit `.env` values.

## 2. Avoid repeats

```powershell
.\.venv\Scripts\python.exe -m pipeline.manage recent --limit 30
```

## 3. Research

Create the run folder `lessons/staging/<YYYY-MM-DD>-<workflow>/` and follow [prompts/research.md](../prompts/research.md). Save notes to `_research.md` in that folder.

## 4. Write lessons

For each topic, write `NN-short-slug.json` in the run folder following:

- [prompts/script_style.md](../prompts/script_style.md)
- [prompts/fill_in_blanks.md](../prompts/fill_in_blanks.md) or [prompts/quiz.md](../prompts/quiz.md)
- [schemas/lesson_schemas.md](../schemas/lesson_schemas.md)

Write JSON with UTF-8 and real French accents. Re-read each script once for factual accuracy against `_research.md`.

## 5. Validate (free, no external calls)

```powershell
.\.venv\Scripts\python.exe -m pipeline.publish --workflow <workflow> --staging lessons/staging/<run-folder> --dry-run
```

Fix every `ERROR`. Review each `WARN` and fix it unless there is a good reason not to (for example, uneven quiz summary lengths should be fixed).

## 6. Publish

```powershell
.\.venv\Scripts\python.exe -m pipeline.publish --workflow <workflow> --staging lessons/staging/<run-folder>
```

The publisher synthesizes audio, uploads to Blob, inserts documents as `pending`, verifies everything, then marks them `published`. On any failure it deletes this run's blobs and documents and writes `runs/<run-id>-FAILED.md`.

## 7. If the run fails

- Read the failure report. Confirm the cleanup lines; if any say `MANUAL CLEANUP NEEDED`, tell the user exactly what is left.
- `401` / `403`: credential problem; stop and tell the user.
- `429` or quota errors: stop; do not retry in a loop (Azure Student quota).
- Content or verification errors: fix the staging JSON, dry-run again, then publish again (one retry).
- Never insert or edit lesson documents in MongoDB by hand.

## 8. Report back to the user

Give: report path (`runs/<run-id>.md`), lesson titles with difficulty and duration, the listen links printed by the publisher (time-limited, do not commit them), warnings worth knowing, and approximate TTS characters used.

## Deleting lessons (only when the user asks)

```powershell
.\.venv\Scripts\python.exe -m pipeline.manage delete --date 2026-10-28                 # preview
.\.venv\Scripts\python.exe -m pipeline.manage delete --date 2026-10-28 --yes           # confirm
.\.venv\Scripts\python.exe -m pipeline.manage delete --lesson-id <id> --yes
.\.venv\Scripts\python.exe -m pipeline.manage delete --run-id <run-id> --yes
```

Always show the preview to the user before running with `--yes`.

## Other helpers

```powershell
.\.venv\Scripts\python.exe -m pipeline.manage link --lesson-id <id>   # fresh listen link
.\.venv\Scripts\python.exe -m pipeline.manage smoke                  # tiny live round trip test
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .        # offline tests
```
