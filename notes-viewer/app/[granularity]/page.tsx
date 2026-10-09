import { notFound } from "next/navigation";
import BucketRow from "@/components/BucketRow";
import Controls from "@/components/Controls";
import {
  buckets,
  GRANULARITIES,
  Granularity,
  orderBuckets,
  parseView,
} from "@/lib/notes";

export function generateStaticParams() {
  return GRANULARITIES.map((granularity) => ({ granularity }));
}

/** Index of every period that contains at least one note. */
export default function GranularityIndex({
  params,
  searchParams,
}: {
  params: { granularity: string };
  searchParams: { restacks?: string; sort?: string; page?: string };
}) {
  const g = params.granularity as Granularity;
  if (!GRANULARITIES.includes(g)) notFound();

  const view = parseView(searchParams);
  const list = buckets(g, view.restacks);
  const ordered = orderBuckets(list, view.sort);

  // Days and weeks are numerous — group them under year headings so the index
  // stays scannable. Months and years are short enough to render flat.
  // Sorting by reactions deliberately drops the grouping: the whole point is a
  // single ranked list, and year headings would chop it into fragments.
  const grouped = (g === "day" || g === "week") && view.sort !== "top";
  const years = [...new Set(ordered.map((b) => b.key.slice(0, 4)))];
  const groups = grouped
    ? years.map((year) => ({
        year,
        items: ordered.filter((b) => b.key.slice(0, 4) === year),
      }))
    : [{ year: "", items: ordered }];

  const total = list.reduce((s, b) => s + b.count, 0);

  return (
    <>
      <Controls granularity={g} view={view} href={(next) => `/${next}`} />

      <div className="period-head">
        <h2>Browse by {g}</h2>
        <div className="summary">
          {list.length} {g}s with activity · {total} notes
          {view.restacks ? " (originals + restacks)" : " (originals only)"}
          {" · "}
          {view.sort === "asc"
            ? "oldest first"
            : view.sort === "top"
            ? "most reactions first"
            : "newest first"}
        </div>
      </div>

      {groups.map(({ year, items }) => (
        <section key={year || "all"} className={grouped ? "year-group" : ""}>
          {year && <h2>{year}</h2>}
          <div className="bucket-list">
            {items.map((b) => (
              <BucketRow key={b.key} granularity={g} bucket={b} view={view} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
