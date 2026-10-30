import { describe, expect, it } from "vitest";
import { cacheKey } from "../lib/cache";
import { gradeBlanks, gradeQuiz } from "../lib/grade";
import { toInternalLesson, toPublicLesson } from "../lib/normalize";

const quiz = {
  lessonId: "quiz-1", workflow: "quiz", status: "published", title: "English", titleFr: "Leçon", difficulty: "B1", createdAt: new Date("2026-01-01"),
  options: ["A", "B", "C", "D"], correctIndex: 1, optionRationales: ["", "Exact", "", ""], explanation: "Le résumé B est fidèle.", scriptFull: "Un texte.",
  audio: { url: "https://example.test/audio.mp3", blobPath: "private.mp3", isPublic: false },
};

describe("public lesson data", () => {
  it("does not expose quiz answers or audio storage details", () => {
    const publicLesson = toPublicLesson(quiz);
    expect(publicLesson).not.toHaveProperty("correctIndex");
    expect(publicLesson).not.toHaveProperty("optionRationales");
    expect(publicLesson).not.toHaveProperty("audio");
  });

  it("grades quiz answers only from the internal document", () => {
    expect(gradeQuiz(toInternalLesson(quiz), 1)?.correct).toBe(true);
    expect(gradeQuiz(toInternalLesson(quiz), 0)?.correct).toBe(false);
    expect(gradeQuiz(toInternalLesson(quiz), 9)).toBeNull();
  });
});

describe("blank grading and cache keys", () => {
  it("accepts case and accent variants but returns the expected answer after grading", () => {
    const lesson = toInternalLesson({ ...quiz, workflow: "fill_in_blanks", passageSegments: [], blanks: [{ index: 1, answer: "Publié", acceptedAnswers: ["publié"] }] });
    const result = gradeBlanks(lesson, { 1: "publie" });
    expect(result?.correctCount).toBe(1);
    expect(result?.results[0].answer).toBe("Publié");
  });

  it("makes filter-sensitive stable cache keys", () => {
    expect(cacheKey("catalog", { workflow: "quiz", page: 1 })).not.toBe(cacheKey("catalog", { workflow: "quiz", page: 2 }));
  });
});
