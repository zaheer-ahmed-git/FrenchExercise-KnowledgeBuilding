import { Catalog } from "@/components/catalog";
import { getCatalog } from "@/lib/db";
import type { CatalogFilters } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const first = (key: string) => typeof params[key] === "string" ? params[key] : undefined;
  const workflow = first("workflow");
  const difficulty = first("difficulty");
  const filters: CatalogFilters = {
    query: first("q"), tag: first("tag"), page: Number(first("page")) || 1,
    workflow: workflow === "quiz" || workflow === "fill_in_blanks" ? workflow : undefined,
    difficulty: difficulty === "B1" || difficulty === "B2" ? difficulty : undefined,
  };
  let result;
  try { result = await getCatalog(filters); } catch { result = { lessons: [], total: 0, page: 1, pageSize: 12 }; }
  return <section className="catalog-page"><div className="hero"><p className="eyebrow">FRANÇAIS · IA · B1–B2</p><h1>Écoutez ce qui change dans l’IA.</h1><p>Des leçons courtes, naturelles et conçues pour entraîner votre compréhension orale.</p></div><Catalog result={result} filters={filters} /></section>;
}
