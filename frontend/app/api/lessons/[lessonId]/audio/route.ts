import { NextResponse } from "next/server";
import { audioUrl } from "@/lib/audio";
import { getInternalLesson } from "@/lib/db";

export const runtime = "nodejs";

export async function GET(_: Request, context: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await context.params;
  try {
    const lesson = await getInternalLesson(lessonId);
    if (!lesson) return NextResponse.json({ error: "Leçon introuvable." }, { status: 404, headers: { "Cache-Control": "no-store" } });
    return NextResponse.redirect(await audioUrl(lesson), { status: 307, headers: { "Cache-Control": "private, max-age=60" } });
  } catch {
    return NextResponse.json({ error: "L’audio est indisponible pour le moment." }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
