# French AI Listening Lessons

Agent-driven content generation for French listening practice (B1–B2) built from recent AI industry developments. Cursor Agent or Codex researches sources, writes lessons, and publishes them with Azure Speech audio (Azure Blob Storage) and MongoDB Atlas documents. Nothing runs on a schedule.

## One-time setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in the values
.\.venv\Scripts\python.exe -m pipeline.manage check
.\.venv\Scripts\python.exe -m pipeline.manage smoke
```

## Running a lesson batch

Open the repo in Cursor or Codex and ask, for example:

- "Generate 3 quiz lessons following the runbook."
- "Create 4 fill-in-the-blank lessons about agentic coding tools from the last two weeks."
- "Delete the lessons created on 2026-10-28."

The agent follows [agent/RUNBOOK.md](agent/RUNBOOK.md). Each successful run writes a report to `runs/` and prints time-limited listen links.

## Layout

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Entry instructions for Cursor and Codex |
| `agent/RUNBOOK.md` | Step-by-step run procedure |
| `prompts/` | Research, French style, fill-in-the-blanks, and quiz prompts |
| `schemas/lesson_schemas.md` | Staging JSON and MongoDB document reference |
| `pipeline/` | `publish` (TTS, Blob, MongoDB, verify, rollback) and `manage` (check, smoke, recent, link, delete) |
| `lessons/staging/` | Agent drafts before publishing (git-ignored) |
| `runs/` | Dated run reports |
| `tests/` | Offline unit tests |

## Costs

Each 6–10 minute lesson is roughly 6,000–8,000 TTS characters, and run reports show the approximate total. On the Azure free Speech tier (0.5 million neural characters per month) that leaves room for about 60 lessons a month. Audio is 24 kHz / 48 kbps mono MP3, so a lesson is about 3 MB.
