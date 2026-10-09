import Link from "next/link";
import { GRANULARITIES, Granularity, qs, SORTS, View } from "@/lib/notes";

/**
 * Granularity tabs + restack and sort toggles. All plain links so the app stays
 * server-rendered and every view is linkable; state lives in the URL.
 */
export default function Controls({
  granularity,
  view,
  href,
}: {
  granularity: Granularity;
  view: View;
  /** Builds the target path when switching granularity. */
  href: (g: Granularity) => string;
}) {
  // Any control change drops back to page 1 — page 4 of a different filter is
  // meaningless and frequently out of range.
  const base = { restacks: view.restacks, sort: view.sort };

  return (
    <div className="controls">
      <nav className="tabs">
        {GRANULARITIES.map((g) => (
          <Link key={g} href={href(g) + qs(base)} data-active={g === granularity}>
            {g}
          </Link>
        ))}
      </nav>

      <Link
        className="toggle"
        data-on={view.restacks}
        href={href(granularity) + qs({ ...base, restacks: !view.restacks })}
      >
        {view.restacks ? "✓ restacks" : "restacks off"}
      </Link>

      <nav className="sorts" aria-label="Sort order">
        {SORTS.map((s) => (
          <Link
            key={s.key}
            href={href(granularity) + qs({ ...base, sort: s.key })}
            data-active={view.sort === s.key}
          >
            {s.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
