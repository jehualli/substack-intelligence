import Link from "next/link";
import { notFound } from "next/navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import BucketRow from "@/components/BucketRow";
import Controls from "@/components/Controls";
import NoteCard from "@/components/NoteCard";
import Pager from "@/components/Pager";
import {
  childGranularity,
  children,
  formatKey,
  GRANULARITIES,
  Granularity,
  isValidKey,
  neighbours,
  notesIn,
  PAGE_SIZE,
  parseView,
  periodKey,
  qs,
} from "@/lib/notes";

export default function PeriodPage({
  params,
  searchParams,
}: {
  params: { granularity: string; key: string };
  searchParams: { restacks?: string; sort?: string; page?: string };
}) {
  const g = params.granularity as Granularity;
  if (!GRANULARITIES.includes(g)) notFound();
  const key = decodeURIComponent(params.key);
  if (!isValidKey(g, key)) notFound();

  const view = parseView(searchParams);
  const q = qs({ restacks: view.restacks, sort: view.sort });
  const path = `/${g}/${key}`;

  const notes = notesIn(g, key, view.restacks, view.sort);
  if (notes.length === 0) notFound();

  // A year holds up to ~1,800 notes. Rendering that is a multi-megabyte page
  // and paginating it is ~37 pages of nothing useful, so a year is presented as
  // a map of its months instead. Finer periods show the notes themselves.
  const asSummary = g === "year";
  const kids = children(g, key, view.restacks, view.sort);
  const childG = childGranularity(g);

  const pages = Math.max(1, Math.ceil(notes.length / PAGE_SIZE));
  const page = Math.min(view.page, pages);
  const shown = asSummary
    ? []
    : notes.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const { newer, older } = neighbours(g, key, view.restacks);
  const [prev, next] = view.sort === "asc" ? [newer, older] : [older, newer];

  const ownCount = notes.filter((n) => n.own).length;
  const reactions = notes.reduce((s, n) => s + n.reactions, 0);

  // Day dividers only help when a page spans more than one day *in order*.
  // Ranked by reactions the notes jump between dates, so the dividers would
  // repeat and mislead — each note carries its own date anyway.
  const showDayHeadings = g !== "day" && view.sort !== "top";
  let lastDay = "";

  return (
    <>
      <Controls
        granularity={g}
        view={view}
        // Switching granularity re-anchors on the same date rather than
        // dumping you back at the index.
        href={(nextG) => `/${nextG}/${periodKey(notes[0].date, nextG)}`}
      />

      <Breadcrumbs granularity={g} periodKey={key} view={view} />

      <div className="period-head">
        <h2>{formatKey(g, key)}</h2>
        <div className="summary">
          {notes.length} note{notes.length === 1 ? "" : "s"}
          {view.restacks &&
            ` · ${ownCount} original, ${notes.length - ownCount} restacked`}
          {" · "}♥ {reactions}
          {!asSummary && pages > 1 && ` · page ${page} of ${pages}`}
        </div>
      </div>

      <div className="pager">
        {prev ? (
          <Link href={`/${g}/${prev}${q}`}>← {formatKey(g, prev)}</Link>
        ) : (
          <span>← nothing earlier</span>
        )}
        {next ? (
          <Link href={`/${g}/${next}${q}`}>{formatKey(g, next)} →</Link>
        ) : (
          <span>nothing later →</span>
        )}
      </div>

      {/* Drill-down: months of a year, days of a month or week. */}
      {kids.length > 0 && childG && (
        <section className="children">
          <h3>
            {kids.length} {childG}
            {kids.length === 1 ? "" : "s"} in this {g}
          </h3>
          <div className="bucket-list">
            {kids.map((b) => (
              <BucketRow
                key={b.key}
                granularity={childG}
                bucket={b}
                view={view}
              />
            ))}
          </div>
        </section>
      )}

      {asSummary ? (
        <p className="note-hint">
          A year holds too many notes to read on one page — open a month above,
          or switch to <Link href={`/month${q}`}>months</Link>,{" "}
          <Link href={`/week${q}`}>weeks</Link> or{" "}
          <Link href={`/day${q}`}>days</Link>.
        </p>
      ) : (
        <>
          {shown.map((n) => {
            const day = n.date.slice(0, 10);
            const heading = showDayHeadings && day !== lastDay ? day : null;
            lastDay = day;
            return (
              <div key={n.id}>
                {heading && (
                  <div className="day-heading">
                    <Link href={`/day/${heading}${q}`}>{heading}</Link>
                  </div>
                )}
                <NoteCard note={n} />
              </div>
            );
          })}
          <Pager page={page} pages={pages} path={path} view={view} />
        </>
      )}
    </>
  );
}
