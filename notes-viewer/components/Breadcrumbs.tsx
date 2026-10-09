import Link from "next/link";
import {
  ancestors,
  formatKeyShort,
  Granularity,
  qs,
  View,
} from "@/lib/notes";

/**
 * Archive › 2026 › July › W30 › Jul 26
 * Every hop up the hierarchy, plus a route back to the current granularity's
 * index — the "get me back to the list" affordance.
 */
export default function Breadcrumbs({
  granularity,
  periodKey,
  view,
}: {
  granularity: Granularity;
  periodKey: string;
  view: View;
}) {
  const q = qs({ restacks: view.restacks, sort: view.sort });
  const trail = ancestors(granularity, periodKey);

  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      <Link href={`/${granularity}${q}`}>All {granularity}s</Link>
      {trail.map((a) => (
        <span key={a.g + a.key}>
          <span className="sep">›</span>
          <Link href={`/${a.g}/${a.key}${q}`}>{formatKeyShort(a.g, a.key)}</Link>
        </span>
      ))}
      <span className="sep">›</span>
      <span className="current">{formatKeyShort(granularity, periodKey)}</span>
    </nav>
  );
}
