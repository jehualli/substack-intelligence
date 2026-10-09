import Link from "next/link";
import { Bucket, formatKey, Granularity, qs, View } from "@/lib/notes";

/** One row in a period index or drill-down strip. */
export default function BucketRow({
  granularity,
  bucket,
  view,
}: {
  granularity: Granularity;
  bucket: Bucket;
  view: View;
}) {
  const q = qs({ restacks: view.restacks, sort: view.sort });
  return (
    <Link className="bucket" href={`/${granularity}/${bucket.key}${q}`}>
      {/* Order matches the .bucket grid columns: 150px | 1fr | auto */}
      <span className="k">{formatKey(granularity, bucket.key)}</span>
      <span className="peek">{bucket.topNote?.body?.slice(0, 150) || "—"}</span>
      <span className="n">
        {bucket.count} note{bucket.count === 1 ? "" : "s"} · ♥ {bucket.reactions}
      </span>
    </Link>
  );
}
