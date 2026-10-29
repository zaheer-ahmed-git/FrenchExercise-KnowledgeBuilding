# Tools & Infrastructure

Stack used by **Cursor Agent / Codex** during manual lesson generation runs, and later by a Vercel application.

## Database — MongoDB Atlas

- Existing Atlas cluster and database.
- **Separate collections** for:
  - Fill-in-the-Blanks lessons
  - Quiz lessons
- Persist: French script, exercise content, blanks / answer keys, quiz options (when applicable), audio URL, creation date, difficulty, source citations, and metadata needed for playback, validation, and future app integration.
- Retention: keep all lessons until the user explicitly requests deletion.

## Audio — Azure Speech Services

- **API** (not Studio click-through): Text-to-Speech with neural French voices.
- Agent may choose / vary high-quality `fr-FR` neural voices across lessons.
- Prefer cost-efficient settings within **Azure Student** quotas.
- Output format: **MP3, 24 kHz / 48 kbps mono** (`audio-24khz-48kbitrate-mono-mp3`), matching the voices' native sample rate, playable in every browser, about 3 MB per lesson. Called through the TTS REST API, with long scripts synthesized in chunks.

## Object storage — Azure Blob Storage

- Store generated audio files.
- MongoDB stores the Blob **URL / path** and related metadata (not the binary itself).

## Caching — Redis

- **Not used** during agent content-generation runs.
- Reserved for the future Vercel application (API response / audio URL caching).

## Deployment (future app)

- **Vercel** for frontend and API routes.
- Not required for agent-driven research → TTS → Blob → MongoDB publishing.

## Credentials & security

- Secrets live in local **`.env`** only (never committed or hardcoded).
- Variables used by `pipeline/`: `MONGODB_URI`, `MONGO_DB_NAME`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_CONTAINER` (falls back to `AZURE_BLOB_CONTAINER`), optional `AUDIO_SAS_HOURS`. See `.env.example`.
- Agents call services only through authenticated APIs.

## Agent tooling (local)

- **Cursor Agent** and **Codex**, run locally when the user instructs a run.
- Reusable research prompts + lightweight scripts/utilities for: research helpers, TTS upload, MongoDB write/validate, cleanup on failure, dated run reports.
- No schedulers, background agents, or heavy orchestration platforms.
