import type { InternalLesson, LessonSummary, PublicLesson, Workflow } from "@/lib/types";

type MongoDate = Date | string | undefined;
type RawDocument = Record<string, unknown>;

function iso(value: MongoDate): string {
  if (!value) return "";
  return value instanceof Date ? value.toISOString() : String(value);
}

function workflowOf(document: RawDocument): Workflow {
  return document.workflow === "fill_in_blanks" ? "fill_in_blanks" : "quiz";
}

export function toSummary(document: RawDocument): LessonSummary {
  return {
    lessonId: String(document.lessonId),
    workflow: workflowOf(document),
    title: String(document.title ?? ""),
    titleFr: String(document.titleFr ?? ""),
    difficulty: document.difficulty === "B2" ? "B2" : "B1",
    topicTags: Array.isArray(document.topicTags) ? document.topicTags.map(String) : [],
    summaryEn: String(document.summaryEn ?? ""),
    createdAt: iso(document.createdAt as MongoDate),
    publishedAt: iso(document.publishedAt as MongoDate) || undefined,
    durationSec: typeof (document.audio as Record<string, unknown> | undefined)?.durationSec === "number"
      ? (document.audio as Record<string, number>).durationSec : undefined,
  };
}

/** Public data intentionally excludes answer keys, correct indexes, rationales and Blob paths. */
export function toPublicLesson(document: RawDocument): PublicLesson {
  const summary = toSummary(document);
  const workflow = summary.workflow;
  return {
    ...summary,
    glossary: Array.isArray(document.glossary) ? document.glossary as PublicLesson["glossary"] : [],
    sources: Array.isArray(document.sources) ? document.sources as PublicLesson["sources"] : [],
    wordCount: Number(document.wordCount ?? 0),
    ...(workflow === "quiz"
      ? { script: String(document.scriptFull ?? ""), question: String(document.question ?? ""), options: (document.options as string[] ?? []).map(String) }
      : {
          passageSegments: Array.isArray(document.passageSegments) ? document.passageSegments as PublicLesson["passageSegments"] : [],
          blankCount: Array.isArray(document.blanks) ? document.blanks.length : 0,
        }),
  };
}

/** Internal representation is only used inside route handlers for signing and grading. */
export function toInternalLesson(document: RawDocument): InternalLesson {
  return {
    ...toPublicLesson(document),
    correctIndex: typeof document.correctIndex === "number" ? document.correctIndex : undefined,
    optionRationales: Array.isArray(document.optionRationales) ? document.optionRationales.map(String) : [],
    explanation: String(document.explanation ?? ""),
    blanks: Array.isArray(document.blanks) ? document.blanks as InternalLesson["blanks"] : [],
    audio: document.audio as InternalLesson["audio"],
  };
}
