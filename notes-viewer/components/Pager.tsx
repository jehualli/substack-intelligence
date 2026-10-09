import Link from "next/link";
import { qs, View } from "@/lib/notes";

/** Page N of M within a single period. Only rendered when there's more than one. */
export default function Pager({
  page,
  pages,
  path,
  view,
}: {
  page: number;
  pages: number;
  path: string;
  view: View;
}) {
  if (pages <= 1) return null;
  const link = (p: number) => path + qs({ ...view, page: p });

  // Window of page numbers around the current one, always including first/last.
  const nums = new Set<number>([1, pages, page]);
  for (let d = 1; d <= 2; d++) {
    if (page - d > 0) nums.add(page - d);
    if (page + d <= pages) nums.add(page + d);
  }
  const ordered = [...nums].sort((a, b) => a - b);

  return (
    <nav className="page-nav" aria-label="Pagination">
      {page > 1 ? (
        <Link href={link(page - 1)}>← Prev</Link>
      ) : (
        <span className="off">← Prev</span>
      )}

      <span className="nums">
        {ordered.map((p, i) => (
          <span key={p}>
            {i > 0 && ordered[i - 1] !== p - 1 && <span className="gap">…</span>}
            {p === page ? (
              <span className="cur">{p}</span>
            ) : (
              <Link href={link(p)}>{p}</Link>
            )}
          </span>
        ))}
      </span>

      {page < pages ? (
        <Link href={link(page + 1)}>Next →</Link>
      ) : (
        <span className="off">Next →</span>
      )}
    </nav>
  );
}
