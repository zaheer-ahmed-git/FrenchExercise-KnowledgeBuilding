export type Workflow = "quiz" | "fill_in_blanks";

export type Source = { title: string; url: string; origin?: string; publishedAt?: string };
export type GlossaryItem = { term: string; definition: string; translationEn?: string };
export type PassageSegment =
  | { type: "text"; value: string }
  | { type: "blank"; index: number };

export type LessonSummary = {
  lessonId: string;
  workflow: Workflow;
  title: string;
  titleFr: string;
  difficulty: "B1" | "B2";
  topicTags: string[];
  summaryEn: string;
  createdAt: string;
  publishedAt?: string;
  durationSec?: number;
};

export type PublicLesson = LessonSummary & {
  glossary: GlossaryItem[];
  sources: Source[];
  wordCount: number;
  script?: string;
  question?: string;
  options?: string[];
  passageSegments?: PassageSegment[];
  blankCount?: number;
};

export type InternalLesson = PublicLesson & {
  correctIndex?: number;
  optionRationales?: string[];
  explanation?: string;
  blanks?: Array<{ index: number; answer: string; acceptedAnswers?: string[]; hint?: string }>;
  audio?: { url: string; blobPath: string; container?: string; isPublic?: boolean };
};

export type CatalogResult = { lessons: LessonSummary[]; total: number; page: number; pageSize: number };

export type CatalogFilters = {
  query?: string;
  workflow?: Workflow;
  difficulty?: "B1" | "B2";
  tag?: string;
  page?: number;
  pageSize?: number;
};
