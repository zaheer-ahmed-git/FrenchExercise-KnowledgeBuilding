# Lesson Schemas

Two layers:

1. **Staging JSON** — what the agent writes, one file per lesson, in `lessons/staging/<run-folder>/NN-slug.json`.
2. **MongoDB document** — what `pipeline.publish` derives and stores. Never write to MongoDB by hand.

Files whose names start with `_` (for example `_research.md`) are ignored by the publisher.

---

## Staging JSON — shared fields

| Field | Required | Notes |
|-------|----------|-------|
| `title` | yes | English title (for the user and reports) |
| `titleFr` | yes | French title shown to the learner |
| `difficulty` | yes | `"B1"` or `"B2"` |
| `topicTags` | no | e.g. `["agents", "open-source", "inference"]` |
| `summaryEn` | no | 1–2 sentence English summary of the lesson topic |
| `sources` | yes | `[{ "title", "url", "origin", "publishedAt" }]` — only URLs actually opened during research |
| `glossary` | no | `[{ "term", "definition", "translationEn" }]` — 6–12 useful terms, French definitions |
| `voiceName` | no | Standard `fr-FR-*Neural` voice; omit to use rotation. HD/Dragon voices are rejected (cost) |
| `speakingRate` | no | SSML rate, default `"-8%"` |

Spoken script length: **750–1500 words** (target 900–1200, about 6–10 minutes at learner pace). Separate paragraphs with a blank line; the audio adds a short pause between paragraphs.

## Staging JSON — `fill_in_blanks`

| Field | Required | Notes |
|-------|----------|-------|
| `scriptMarked` | yes | Full French script with **10–15** inline blanks: `[[answer]]` or `[[answer\|hint]]` |

The audio speaks the answers; the learner sees blanks. Example fragment:

```json
{
  "scriptMarked": "Cette semaine, plusieurs laboratoires [[ont publié|verbe, passé composé]] de nouveaux modèles.\n\n[[Cependant|connecteur]], les chercheurs restent prudents..."
}
```

Rules: no nested or partial markers; answers of 1–3 words; spread blanks across the whole script.

## Staging JSON — `quiz`

| Field | Required | Notes |
|-------|----------|-------|
| `script` | yes | Full French script (plain text, no markers) |
| `question` | no | Defaults to "Quel résumé correspond le mieux à ce que vous avez entendu ?" |
| `options` | yes | Exactly 4: `[{ "text", "isCorrect", "rationale" }]`, exactly one `isCorrect: true` |
| `explanation` | no | Short French explanation shown after answering |

The publisher shuffles option order, so the correct option can be written first.

---

## MongoDB documents

Collections: `fill_in_blank_lessons`, `quiz_lessons` (database from `MONGO_DB_NAME`). Indexes: unique `lessonId`, `(status, createdAt desc)`, `runId`.

Shared fields:

```text
_id, lessonId, runId, workflow, status ("pending" -> "published"), publishedAt,
title, titleFr, difficulty, language ("fr-FR"), topicTags, summaryEn, glossary,
sources, createdAt, scriptFull, wordCount,
audio: { url, blobPath, container, isPublic, contentType, format, bytes,
         durationSec, voiceName, speakingRate, ttsCharacters, ttsRequests }
```

`fill_in_blank_lessons` extra:

```text
passageWithBlanks   display text with "______ (n)" placeholders
passageSegments     [{type: "text", value} | {type: "blank", index}]  (for app rendering)
blanks              [{index, answer, acceptedAnswers, hint}]
```

`quiz_lessons` extra:

```text
question, options[4], correctIndex (0-3), optionRationales[4], explanation
```

Apps must only read `status: "published"` documents. If the container is private, `audio.url` needs a SAS token at read time (`python -m pipeline.manage link --lesson-id <id>`, or server-side signing in the future Vercel API).
