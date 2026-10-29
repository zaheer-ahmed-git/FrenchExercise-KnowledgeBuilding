# Fill-in-the-Blanks Lesson Prompt

Write one staging JSON file per lesson. Follow [script_style.md](script_style.md) and the schema in [schemas/lesson_schemas.md](../schemas/lesson_schemas.md).

## Blanks

- **10–15 blanks** per lesson, written inline as `[[answer]]` or `[[answer|hint]]`.
- Spread them evenly; none in the first two sentences (let the listener settle in).
- Mix categories across the lesson:
  - conjugated verbs (*ont développé, pourrait, soit*)
  - connectors and adverbs (*cependant, désormais, pourtant*)
  - everyday vocabulary and collocations (*prendre en compte, mettre en place*)
  - technical vocabulary explained in the script (*jeu de données, inférence*)
  - small grammar traps heard in speech (*qu'ils, ce qui / ce que, liaison words*)
- Answers are 1–3 words, clearly audible, and unambiguous in context.
- Hints are short French labels: `verbe, passé composé`, `connecteur`, `nom féminin`, `expression`.

## Glossary

Add 6–12 `glossary` entries for the hardest words in the script: French definition plus English translation.

## Output

```json
{
  "title": "...",
  "titleFr": "...",
  "difficulty": "B1",
  "topicTags": ["..."],
  "summaryEn": "...",
  "sources": [{"title": "...", "url": "https://...", "origin": "Hugging Face Blog", "publishedAt": "2026-10-20"}],
  "glossary": [{"term": "...", "definition": "...", "translationEn": "..."}],
  "scriptMarked": "Paragraphe 1...\n\nParagraphe 2 avec un [[mot|nom masculin]]..."
}
```

Use `B1` for gentler topics and `B2` for denser technical ones; aim for a mix across a run.
