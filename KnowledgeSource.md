# Knowledge Sources & Research Guidance

Guidance for **Cursor Agent / Codex** when researching content for French listening lessons. Research is **English-first**; output scripts are **French (B1–B2)**.

## Topic focus

Recent advancements in:

- Artificial intelligence and machine learning
- Generative AI and LLMs
- Agentic systems and related tooling
- Closely related software / systems topics when they strengthen the lesson

Prioritize: **accuracy**, **technical depth**, **recency**, and **educational value**.

## Primary source categories

### Expert reports & emerging tech

- **arXiv** (e.g. cs.AI, cs.CL, cs.LG) — API / RSS
- **Papers with Code** (when useful for grounding claims)
- **First-party lab & cloud blogs** (RSS/JSON where available):
  - AI labs: OpenAI, Anthropic, Google DeepMind / Google Research, Hugging Face, AI at Meta
  - Cloud / enterprise ML blogs when relevant (AWS, Google Cloud, Microsoft)

High-signal filters (optional): daily.dev (#ai), Import AI, The Batch (DeepLearning.AI).

### Developer forums & adoption signals

- **Hacker News** — top submissions and substantive discussion
- **Reddit** — e.g. r/MachineLearning, r/LocalLLaMA, r/artificial, r/webdev (treat as sentiment / trend signal; verify claims)
- **GitHub Trending** — sudden adoption of frameworks, libraries, and tools

### YouTube (preferred channels)

Use titles, descriptions, metadata, and transcripts (e.g. `youtube-transcript-api`) — not full video downloads.

**Frontier research & AI labs**

- OpenAI, Anthropic, Google Research, Hugging Face, AI at Meta, Stanford Online, Harvard University

**AI architecture & systems**

- Andrej Karpathy, Hussein Nasser, ByteByteGo, Gaurav Sen, LangChain

**Applied AI & agents**

- Matthew Berman, Matt Wolfe, AI Jason, David Ondrej, AICodeKing, TheAIGRID, Skill Leap AI, Ben AI

**Software engineering**

- Fireship, Traversy Media, Matt Pocock, ArjanCodes, Web Dev Simplified, Hitesh Choudhary, CodeWithHarry, Academind, mCoding

**Technology & startups**

- Y Combinator, YC Root Access

The agent may add other high-quality channels when clearly relevant. Prefer channels that match the lesson’s technical depth.

## Reusable research brief (for Cursor / Codex)

When the user asks to run a content generation for a workflow, research should:

1. **Discover** recent items across the sources above (last days/weeks unless the user specifies otherwise).
2. **Evaluate** credibility and technical value; discard hype, duplicates, and unverified claims.
3. **Select** enough material for **3–4** distinct lessons (same workflow per run).
4. **Synthesize** cohesive French scripts (~6–10 minutes speaking length each), educational for B1–B2.
5. **Cite** sources used (title, origin, URL/date when available) for MongoDB metadata and the run report.
6. **Adapt to workflow**:
   - **Fill-in-the-Blanks:** script + selective blanks + answer key (flexible mix of everyday and technical language).
   - **Quiz:** same audio script + four French summaries (one correct, three plausible distractors).

## Agent pipeline (manual, per instruction)

Not a scheduled platform — steps the agent performs when asked:

1. **Ingest / research** — pull and filter from the sources above.
2. **Synthesize** — English findings → French lesson scripts (B1–B2).
3. **Exercise layer** — blanks + key, or quiz options, per workflow.
4. **Audio** — Azure Speech Services TTS → MP3/WAV.
5. **Publish** — upload audio to Azure Blob; write documents to the matching MongoDB collection.
6. **Validate** — audio URL reachable; documents queryable; answers consistent with the script.
7. **Report** — dated summary of titles, sources, files, DB records, and outcome.
8. **On failure** — abort; clean up incomplete Blob objects and MongoDB docs where possible (all-or-nothing).

## Out of scope here

- Cron / background scheduling
- Redis caching (future Vercel app only)
- Building the learner-facing Vercel UI during research runs
