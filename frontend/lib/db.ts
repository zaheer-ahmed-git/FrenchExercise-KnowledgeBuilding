import { MongoClient, type Document } from "mongodb";
import { cacheKey, cached } from "@/lib/cache";
import { toInternalLesson, toPublicLesson, toSummary } from "@/lib/normalize";
import type { CatalogFilters, CatalogResult, InternalLesson, PublicLesson, Workflow } from "@/lib/types";

const COLLECTIONS: Record<Workflow, string> = {
  quiz: "quiz_lessons",
  fill_in_blanks: "fill_in_blank_lessons",
};

const globalForMongo = global as typeof globalThis & { mongoClient?: MongoClient };

function database() {
  const uri = process.env.MONGODB_URI;
  if (!uri) throw new Error("MONGODB_URI is not configured");
  globalForMongo.mongoClient ??= new MongoClient(uri, { appName: "french-listening-vercel" });
  return globalForMongo.mongoClient.db(process.env.MONGO_DB_NAME || "french_learning");
}

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

type NormalizedFilters = {
  query: string; workflow?: Workflow; difficulty?: "B1" | "B2"; tag: string; page: number; pageSize: number;
};

function cleanedFilters(filters: CatalogFilters): NormalizedFilters {
  return {
    query: (filters.query ?? "").trim().slice(0, 80),
    workflow: filters.workflow === "fill_in_blanks" ? "fill_in_blanks" : filters.workflow === "quiz" ? "quiz" : undefined,
    difficulty: filters.difficulty === "B2" ? "B2" : filters.difficulty === "B1" ? "B1" : undefined,
    tag: (filters.tag ?? "").trim().slice(0, 60),
    page: Math.min(Math.max(Number(filters.page) || 1, 1), 1000),
    pageSize: Math.min(Math.max(Number(filters.pageSize) || 12, 1), 24),
  };
}

function catalogQuery(filters: NormalizedFilters): Document {
  const common: Document = { status: "published" };
  if (filters.difficulty) common.difficulty = filters.difficulty;
  if (filters.tag) common.topicTags = filters.tag;
  if (filters.query) {
    const matcher = { $regex: escapeRegex(filters.query), $options: "i" };
    common.$or = [{ titleFr: matcher }, { title: matcher }, { topicTags: matcher }];
  }
  return common;
}

export async function getCatalog(filters: CatalogFilters = {}): Promise<CatalogResult> {
  const input = cleanedFilters(filters);
  return cached(cacheKey("catalog", input), 300, async () => {
    const db = database();
    const workflows: Workflow[] = input.workflow ? [input.workflow] : ["quiz", "fill_in_blanks"];
    const query = catalogQuery(input);
    const pages = await Promise.all(workflows.map(async (workflow) => {
      const collection = db.collection(COLLECTIONS[workflow]);
      return collection.find(query, { projection: { _id: 0, lessonId: 1, workflow: 1, title: 1, titleFr: 1, difficulty: 1, topicTags: 1, summaryEn: 1, createdAt: 1, publishedAt: 1, "audio.durationSec": 1 } }).toArray();
    }));
    const all = pages.flat().map(toSummary).sort((a, b) => (b.publishedAt || b.createdAt).localeCompare(a.publishedAt || a.createdAt));
    const start = (input.page - 1) * input.pageSize;
    return { lessons: all.slice(start, start + input.pageSize), total: all.length, page: input.page, pageSize: input.pageSize };
  });
}

async function sourceLesson(lessonId: string): Promise<Document | null> {
  const db = database();
  const query = { lessonId, status: "published" };
  const [quiz, blanks] = await Promise.all([
    db.collection(COLLECTIONS.quiz).findOne(query),
    db.collection(COLLECTIONS.fill_in_blanks).findOne(query),
  ]);
  return quiz || blanks;
}

export async function getPublicLesson(lessonId: string): Promise<PublicLesson | null> {
  return cached(cacheKey("lesson", lessonId), 600, async () => {
    const document = await sourceLesson(lessonId);
    return document ? toPublicLesson(document) : null;
  });
}

export async function getInternalLesson(lessonId: string): Promise<InternalLesson | null> {
  const document = await sourceLesson(lessonId);
  return document ? toInternalLesson(document) : null;
}
