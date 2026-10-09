// Imported rather than read from disk at request time: on Vercel each route runs
// in its own bundle, and a runtime fs read of a path relative to cwd is not
// reliably traced into it. A static import makes the bundler ship the data.
import notesData from "@/data/notes.json";

export type Note = {
  id: number;
  date: string;
  body: string;
  reactions: number;
  restacks: number;
  replies: number;
  own: boolean;
  author: string | null;
  handle: string | null;
};

export type Granularity = "day" | "week" | "month" | "year";

export const GRANULARITIES: Granularity[] = ["day", "week", "month", "year"];

/** desc = newest first, asc = oldest first, top = most reactions first. */
export type SortDir = "desc" | "asc" | "top";

export const SORTS: { key: SortDir; label: string }[] = [
  { key: "desc", label: "↓ Newest" },
  { key: "asc", label: "↑ Oldest" },
  { key: "top", label: "♥ Top" },
];

/** Notes per page on period pages. Days never reach it; months run to ~6 pages. */
export const PAGE_SIZE = 50;

const NOTES = notesData as Note[];

export function allNotes(): Note[] {
  return NOTES;
}

// --- period keys -----------------------------------------------------------
// day   2026-07-26
// week  2026-W30   (ISO week, Monday-start)
// month 2026-07
// year  2026

/** ISO-8601 week key. Weeks belong to the year containing their Thursday. */
export function isoWeekKey(iso: string): string {
  const d = new Date(iso.slice(0, 10) + "T00:00:00Z");
  const day = d.getUTCDay() || 7; // Sunday = 7
  d.setUTCDate(d.getUTCDate() + 4 - day); // shift to that week's Thursday
  const year = d.getUTCFullYear();
  const jan1 = Date.UTC(year, 0, 1);
  const week = Math.ceil(((d.getTime() - jan1) / 86400000 + 1) / 7);
  return `${year}-W${String(week).padStart(2, "0")}`;
}

export function periodKey(iso: string, g: Granularity): string {
  switch (g) {
    case "day":
      return iso.slice(0, 10);
    case "week":
      return isoWeekKey(iso);
    case "month":
      return iso.slice(0, 7);
    case "year":
      return iso.slice(0, 4);
  }
}

/** Monday..Sunday date range covered by an ISO week key, for display. */
export function weekRange(key: string): { start: string; end: string } {
  const [y, w] = key.split("-W").map(Number);
  const jan4 = new Date(Date.UTC(y, 0, 4));
  const jan4Day = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - jan4Day + 1 + (w - 1) * 7);
  const sunday = new Date(monday);
  sunday.setUTCDate(monday.getUTCDate() + 6);
  return {
    start: monday.toISOString().slice(0, 10),
    end: sunday.toISOString().slice(0, 10),
  };
}

export function isValidKey(g: Granularity, key: string): boolean {
  const patterns: Record<Granularity, RegExp> = {
    day: /^\d{4}-\d{2}-\d{2}$/,
    week: /^\d{4}-W\d{2}$/,
    month: /^\d{4}-\d{2}$/,
    year: /^\d{4}$/,
  };
  return patterns[g].test(key);
}

// --- bucketing -------------------------------------------------------------

export type Bucket = {
  key: string;
  count: number;
  ownCount: number;
  reactions: number;
  topNote: Note | null;
};

/**
 * Groups notes into period buckets, newest first.
 * `includeRestacks` filters the corpus before bucketing so counts always match
 * what the page will actually render.
 */
export function buckets(g: Granularity, includeRestacks: boolean): Bucket[] {
  const notes = allNotes().filter((n) => includeRestacks || n.own);
  const map = new Map<string, Note[]>();

  for (const n of notes) {
    const k = periodKey(n.date, g);
    const existing = map.get(k);
    if (existing) existing.push(n);
    else map.set(k, [n]);
  }

  return [...map.entries()]
    .map(([key, ns]) => ({
      key,
      count: ns.length,
      ownCount: ns.filter((n) => n.own).length,
      reactions: ns.reduce((s, n) => s + n.reactions, 0),
      topNote: ns.reduce<Note | null>(
        (best, n) => (!best || n.reactions > best.reactions ? n : best),
        null
      ),
    }))
    .sort((a, b) => (a.key < b.key ? 1 : -1));
}

export function notesIn(
  g: Granularity,
  key: string,
  includeRestacks: boolean,
  sort: SortDir = "desc"
): Note[] {
  const found = allNotes().filter(
    (n) => (includeRestacks || n.own) && periodKey(n.date, g) === key
  );
  // allNotes() is stored newest-first, so desc needs no work.
  if (sort === "asc") return found.slice().reverse();
  if (sort === "top")
    // Ties broken by recency, since `found` is already newest-first and sort()
    // is stable — equal-reaction notes keep chronological order.
    return found.slice().sort((a, b) => b.reactions - a.reactions);
  return found;
}

/** Applies the active sort to a period index or drill-down list. */
export function orderBuckets(list: Bucket[], sort: SortDir): Bucket[] {
  if (sort === "asc") return [...list].reverse();
  if (sort === "top")
    return [...list].sort((a, b) => b.reactions - a.reactions);
  return list;
}

// --- hierarchy -------------------------------------------------------------

/**
 * Ancestor periods of a key, coarsest first — the breadcrumb trail.
 * Weeks are deliberately not given a month ancestor: an ISO week can straddle
 * two months, so any single answer would be wrong half the time.
 */
export function ancestors(
  g: Granularity,
  key: string
): { g: Granularity; key: string }[] {
  switch (g) {
    case "day":
      return [
        { g: "year", key: key.slice(0, 4) },
        { g: "month", key: key.slice(0, 7) },
        { g: "week", key: isoWeekKey(key) },
      ];
    case "week":
      return [{ g: "year", key: key.slice(0, 4) }];
    case "month":
      return [{ g: "year", key: key.slice(0, 4) }];
    case "year":
      return [];
  }
}

/** The granularity one step finer, used for drill-down strips. */
export function childGranularity(g: Granularity): Granularity | null {
  return g === "year" ? "month" : g === "month" ? "day" : g === "week" ? "day" : null;
}

/**
 * Child periods contained in this one, derived from the notes themselves so
 * only periods that actually hold something are listed.
 */
export function children(
  g: Granularity,
  key: string,
  includeRestacks: boolean,
  sort: SortDir = "desc"
): Bucket[] {
  const child = childGranularity(g);
  if (!child) return [];
  const inside = new Set(
    notesIn(g, key, includeRestacks).map((n) => periodKey(n.date, child))
  );
  const list = buckets(child, includeRestacks).filter((b) => inside.has(b.key));
  return orderBuckets(list, sort);
}

/** Previous/next period keys that actually contain notes — skips empty gaps. */
export function neighbours(g: Granularity, key: string, includeRestacks: boolean) {
  const keys = buckets(g, includeRestacks).map((b) => b.key); // newest first
  const i = keys.indexOf(key);
  return {
    newer: i > 0 ? keys[i - 1] : null,
    older: i >= 0 && i < keys.length - 1 ? keys[i + 1] : null,
    index: i,
    total: keys.length,
  };
}

// --- view state in the URL -------------------------------------------------

export type View = { restacks: boolean; sort: SortDir; page: number };

export function parseView(sp: {
  restacks?: string;
  sort?: string;
  page?: string;
}): View {
  const page = Number(sp.page);
  return {
    restacks: sp.restacks === "1",
    sort: sp.sort === "asc" ? "asc" : sp.sort === "top" ? "top" : "desc",
    page: Number.isFinite(page) && page > 1 ? Math.floor(page) : 1,
  };
}

/** Serialises view state, omitting defaults so clean URLs stay clean. */
export function qs(v: Partial<View>): string {
  const p = new URLSearchParams();
  if (v.restacks) p.set("restacks", "1");
  if (v.sort && v.sort !== "desc") p.set("sort", v.sort);
  if (v.page && v.page > 1) p.set("page", String(v.page));
  const s = p.toString();
  return s ? `?${s}` : "";
}

/** Compact label for breadcrumbs, where the parent already gives context. */
export function formatKeyShort(g: Granularity, key: string): string {
  if (g === "day") {
    return new Date(key + "T00:00:00Z").toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    });
  }
  if (g === "week") return "W" + key.split("-W")[1];
  if (g === "month") {
    return new Date(key + "-01T00:00:00Z").toLocaleDateString("en-US", {
      month: "long",
      timeZone: "UTC",
    });
  }
  return key;
}

export function formatKey(g: Granularity, key: string): string {
  if (g === "day") {
    return new Date(key + "T00:00:00Z").toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    });
  }
  if (g === "week") {
    const { start, end } = weekRange(key);
    const fmt = (s: string) =>
      new Date(s + "T00:00:00Z").toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      });
    return `${key} · ${fmt(start)} – ${fmt(end)}`;
  }
  if (g === "month") {
    return new Date(key + "-01T00:00:00Z").toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      timeZone: "UTC",
    });
  }
  return key;
}
