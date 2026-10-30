import { NextRequest, NextResponse } from "next/server";
import { getCatalog } from "@/lib/db";
import type { CatalogFilters } from "@/lib/types";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const workflow = searchParams.get("workflow");
  const difficulty = searchParams.get("difficulty");
  const filters: CatalogFilters = {
    query: searchParams.get("q") ?? undefined,
    workflow: workflow === "quiz" || workflow === "fill_in_blanks" ? workflow : undefined,
    difficulty: difficulty === "B1" || difficulty === "B2" ? difficulty : undefined,
    tag: searchParams.get("tag") ?? undefined,
    page: Number(searchParams.get("page")) || 1,
    pageSize: Number(searchParams.get("pageSize")) || 12,
  };
  try {
    const result = await getCatalog(filters);
    return NextResponse.json(result, { headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600" } });
  } catch {
    return NextResponse.json({ error: "Le catalogue est indisponible pour le moment." }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
