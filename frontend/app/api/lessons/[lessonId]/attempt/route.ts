import { NextResponse } from "next/server";
import { getInternalLesson } from "@/lib/db";
import { gradeBlanks, gradeQuiz } from "@/lib/grade";

export const runtime = "nodejs";

export async function POST(request: Request, context: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await context.params;
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Réponse invalide." }, { status: 400, headers: { "Cache-Control": "no-store" } }); }
  const lesson = await getInternalLesson(lessonId);
  if (!lesson) return NextResponse.json({ error: "Leçon introuvable." }, { status: 404, headers: { "Cache-Control": "no-store" } });
  const payload = body as { optionIndex?: unknown; answers?: unknown };
  const result = lesson.workflow === "quiz" ? gradeQuiz(lesson, payload.optionIndex) : gradeBlanks(lesson, payload.answers);
  if (!result) return NextResponse.json({ error: "Réponse invalide." }, { status: 400, headers: { "Cache-Control": "no-store" } });
  return NextResponse.json(result, { headers: { "Cache-Control": "no-store" } });
}
