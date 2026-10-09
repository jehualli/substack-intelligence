// Copies the pipeline's corpus into the app and strips fields the viewer doesn't use.
// Run automatically before dev/build, or on demand with `npm run sync`.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../substack_notes_all.json");
const OUT = resolve(here, "../data/notes.json");
const AUTHOR_ID = 273636371;

// Deployed standalone (Vercel), the pipeline corpus one level up isn't present.
// data/notes.json ships with the project, so use it as-is rather than failing.
if (!existsSync(SRC)) {
  if (existsSync(OUT)) {
    const n = JSON.parse(readFileSync(OUT, "utf8")).length;
    console.log(`[build-data] no ${SRC} — using committed data/notes.json (${n} notes)`);
    process.exit(0);
  }
  console.error(`[build-data] missing both ${SRC} and ${OUT} — nothing to build`);
  process.exit(1);
}

const raw = JSON.parse(readFileSync(SRC, "utf8"));

const notes = raw
  .filter((n) => n.date)
  .map((n) => ({
    id: n.id,
    date: n.date,
    body: n.body ?? "",
    reactions: n.reactions ?? 0,
    restacks: n.restacks ?? 0,
    replies: n.replies ?? 0,
    own: n.author_id === AUTHOR_ID,
    author: n.author_id === AUTHOR_ID ? null : n.author_name || "unknown",
    handle: n.author_id === AUTHOR_ID ? null : n.author_handle || null,
  }))
  .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(notes));

const own = notes.filter((n) => n.own).length;
console.log(
  `[build-data] ${notes.length} notes (${own} original, ${notes.length - own} restacks) ` +
    `${notes[notes.length - 1].date.slice(0, 10)} → ${notes[0].date.slice(0, 10)}`
);
