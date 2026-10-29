# Agent Instructions

This repository produces French listening lessons (B1–B2) about recent AI developments. Lessons are created only when the user explicitly asks for a run. There is no scheduler.

- To generate, publish, or delete lessons, follow [agent/RUNBOOK.md](agent/RUNBOOK.md) step by step.
- Product intent: [InitialPlan.md](InitialPlan.md). Services: [Tools.md](Tools.md). Sources: [KnowledgeSource.md](KnowledgeSource.md).
- Publish only through `python -m pipeline.publish`; it handles TTS, Blob upload, MongoDB, verification, and rollback.
- Secrets live in `.env`. Never print, commit, or hardcode them, and never commit SAS listen links.
- Commands must work in Windows PowerShell; chain with `;`.
- Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .` after changing code in `pipeline/`.
