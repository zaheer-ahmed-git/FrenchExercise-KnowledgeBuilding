# Research Prompt

Use this to find material for one run. Sources and channels: [KnowledgeSource.md](../KnowledgeSource.md).

## Inputs

- Workflow (`fill_in_blanks` or `quiz`) and lesson count (default **3**, max 4)
- Optional focus or time window from the user (default: **last 14 days**)
- Topics already covered: output of `python -m pipeline.manage recent --limit 30`

## Steps

1. **Scan widely.** Use web search plus direct visits to: arXiv listings (cs.AI, cs.CL, cs.LG), first-party lab blogs (OpenAI, Anthropic, Google DeepMind / Research, Hugging Face, Meta AI), Hacker News front page and top AI threads, Reddit (r/MachineLearning, r/LocalLLaMA, r/artificial), GitHub Trending, and recent uploads from the preferred YouTube channels. Include the current month and year in search queries.
2. **Shortlist 6–8 candidates.** For each: what happened, who, when, why it matters, primary source URL.
3. **Verify.** Confirm each claim against a primary source (paper, official post, repository, or the video itself). Treat Reddit, HN, and influencer videos as signals, not proof. Drop anything you cannot verify, anything older than the window unless it is essential context, and topics already in the `recent` list.
4. **Pick distinct topics.** Choose the requested number with variety, for example one research result, one product or model release, one developer-tooling or open-source trend, one systems or architecture idea. Avoid two lessons on the same announcement.
5. **Record notes.** Write `lessons/staging/<run-folder>/_research.md` with, per chosen topic: key facts (numbers, names, dates), 2–4 source URLs, and what a learner should take away.

## Quality bar

- Accuracy over excitement: no invented numbers, benchmarks, quotes, or release dates.
- Cite only URLs you actually opened. If a YouTube transcript is unavailable, use the title, description, and any linked primary source.
- Prefer explanations of *how* and *why* (architecture, trade-offs, implications) over announcement lists.
- Every lesson must stand alone: a learner who missed the news should still follow it.
