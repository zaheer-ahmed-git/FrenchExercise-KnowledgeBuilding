import { notFound } from "next/navigation";
import { LessonExperience } from "@/components/lesson-experience";
import { getPublicLesson } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function LessonPage({ params }: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await params;
  const lesson = await getPublicLesson(lessonId);
  if (!lesson) notFound();
  return <LessonExperience lesson={lesson} />;
}
