import type { InternalLesson } from "@/lib/types";

const fold = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr-FR").replace(/[’']/g, "'").replace(/[^\p{L}\p{N}' ]/gu, "").replace(/\s+/g, " ").trim();

export function gradeQuiz(lesson: InternalLesson, optionIndex: unknown) {
  if (typeof optionIndex !== "number" || !Number.isInteger(optionIndex) || optionIndex < 0 || optionIndex >= (lesson.options?.length ?? 0)) return null;
  const correctIndex = lesson.correctIndex;
  if (correctIndex === undefined) return null;
  return {
    correct: optionIndex === correctIndex,
    correctIndex,
    optionRationale: lesson.optionRationales?.[optionIndex] ?? "",
    explanation: lesson.explanation ?? "",
  };
}

export function gradeBlanks(lesson: InternalLesson, submitted: unknown) {
  if (!submitted || typeof submitted !== "object" || Array.isArray(submitted)) return null;
  const answers = submitted as Record<string, unknown>;
  const blanks = lesson.blanks ?? [];
  if (!blanks.length) return null;
  const results = blanks.map((blank) => {
    const submittedValue = answers[String(blank.index)];
    const value = typeof submittedValue === "string" ? submittedValue : "";
    const allowed = blank.acceptedAnswers?.length ? blank.acceptedAnswers : [blank.answer];
    return { index: blank.index, correct: allowed.some((answer) => fold(answer) === fold(value)), answer: blank.answer, hint: blank.hint };
  });
  return { results, correctCount: results.filter((result) => result.correct).length, total: results.length };
}
