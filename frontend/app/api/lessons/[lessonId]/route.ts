import { NextResponse } from "next/server";
import { getPublicLesson } from "@/lib/db";

export const runtime = "nodejs";

export async function GET(_: Request, context: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await context.params;
  try {
    const lesson = await getPublicLesson(lessonId);
    if (!lesson) return NextResponse.json({ error: "Leçon introuvable." }, { status: 404, headers: { "Cache-Control": "no-store" } });
    return NextResponse.json(lesson, { headers: { "Cache-Control": "public, s-maxage=600, stale-while-revalidate=1200" } });
  } catch {
    return NextResponse.json({ error: "La leçon est indisponible pour le moment." }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
