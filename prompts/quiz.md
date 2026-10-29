# Audio Comprehension Quiz Prompt

Write one staging JSON file per lesson. Follow [script_style.md](script_style.md) and the schema in [schemas/lesson_schemas.md](../schemas/lesson_schemas.md).

## The four summaries

- Each summary is **60–90 words** in French, with similar length, structure, and register, so form gives nothing away.
- **Correct option:** faithfully paraphrases the main points of the whole script; it must not copy sentences word for word.
- **Three distractors:** each mostly faithful, but with one or two meaningful errors that only careful listening catches. Use a different trap for each:
  - wrong detail (number, organization, date, order of events)
  - reversed cause and effect, or a reversed conclusion
  - a claim the script never made, or an overstated nuance (*"toujours"* vs *"parfois"*)
  - a key point omitted and replaced by a secondary one
- No distractor may be absurd or contradict common sense; all four must sound plausible to someone who half-listened.
- `rationale` (French, 1–2 sentences) explains why each option is right or wrong, quoting the relevant idea from the script.
- `explanation` (French, 2–3 sentences) summarizes what the learner should have noticed.

## Glossary

Add 6–12 `glossary` entries for difficult words heard in the audio.

## Output

```json
{
  "title": "...",
  "titleFr": "...",
  "difficulty": "B2",
  "topicTags": ["..."],
  "summaryEn": "...",
  "sources": [{"title": "...", "url": "https://...", "origin": "arXiv", "publishedAt": "2026-10-21"}],
  "glossary": [{"term": "...", "definition": "...", "translationEn": "..."}],
  "script": "Paragraphe 1...\n\nParagraphe 2...",
  "options": [
    {"text": "...", "isCorrect": true, "rationale": "..."},
    {"text": "...", "isCorrect": false, "rationale": "..."},
    {"text": "...", "isCorrect": false, "rationale": "..."},
    {"text": "...", "isCorrect": false, "rationale": "..."}
  ],
  "explanation": "..."
}
```

The publisher shuffles option order automatically.
