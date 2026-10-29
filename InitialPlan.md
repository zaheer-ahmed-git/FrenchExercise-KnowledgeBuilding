# Initial Plan — AI Industry French Listening Platform

## Product goal

Build a platform that combines **AI industry research with French listening practice**.

Stay current on AI, machine learning, generative AI, LLMs, agentic systems, and related technologies while improving French listening, vocabulary, and comprehension at **B1–B2** (from an **A2** starting level).

## Two learning workflows

Each agent run targets **exactly one** workflow, as specified in the user’s instructions.

### 1. Listening with Fill-in-the-Blanks

- Generate **3–4** French passages (~**6–10 minutes** each) based on recent industry developments.
- Produce matching audio (Azure Speech TTS).
- Display the passage with blanks (everyday French, phrases, structures, vocabulary, and technical terms — flexible mix).
- Store the full script, blanks, and answer key for validation and future app playback.

### 2. Audio Comprehension Quiz

- Generate **3–4** French audio lessons (~**6–10 minutes** each) from the same research pipeline.
- After listening, present **four French summaries** derived from that audio script.
- Exactly **one** summary is correct; the other three are plausible distractors.
- The learner must listen carefully to choose the right option.

## Content principles

- Research primarily in **English** from curated high-signal sources.
- Transform findings into **natural, educational French** scripts suitable for B1–B2 progression (clear explanations, accessible vocabulary, gradual technical depth).
- Prefer accuracy, technical depth, recency, and educational value.
- Keep all lessons indefinitely unless the user explicitly asks to delete specific lessons or date ranges.

## How content is produced (agent-driven, not scheduled)

There is **no** cron, background agent, or dedicated always-on content pipeline.

Whenever the user opens the repository and **explicitly** instructs Cursor Agent or Codex (local):

1. Research recent, credible AI/tech developments.
2. Synthesize French lesson scripts for the chosen workflow.
3. Generate audio via **Azure Speech Services API**.
4. Upload audio to **Azure Blob Storage**.
5. Write validated lesson documents to **MongoDB Atlas** (separate collections per workflow).
6. Emit a concise dated run report (titles, sources, files, DB records, result).
7. On any critical failure: **fail the run**, clean up incomplete uploads/records where possible (all-or-nothing).

Reusable research prompts and lightweight utilities support these steps. Agents perform the work directly when asked.

## Future application (out of scope for content runs)

A future **Vercel** app (API + frontend) will consume MongoDB lessons and Blob audio URLs. **Redis** is reserved for that app’s caching — not for manual generation runs.

## Success criteria for one run

- ~3–4 complete lessons for the selected workflow.
- Playable audio in Azure Blob Storage.
- Queryable, validated MongoDB documents (script, exercise data, answers, audio URL, metadata, citations).
- Dated report of what was produced.
- Cost-aware use of Azure Student subscription quotas and credits.
