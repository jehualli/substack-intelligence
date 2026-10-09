# notes-viewer

Next.js 14 reader for the scraped note corpus. Browse every note by **day, week,
month or year**, sort by date or reactions, with restacks toggleable.

**Live:** https://glo-notes-archive.vercel.app

```bash
nvm use 22
npm install
npm run dev      # http://localhost:3005
```

`npm run dev` and `npm run build` both run `scripts/build-data.mjs` first, which
copies `../substack_notes_all.json` into `data/notes.json` and drops the fields
the viewer doesn't use. After re-scraping, restart dev or run `npm run sync`.

## Routes

| Route | What it shows |
|-------|---------------|
| `/` | redirects to `/month` |
| `/day`, `/week`, `/month`, `/year` | index of every period containing notes, with count, total reactions and a preview of that period's top note |
| `/day/2026-07-26` | every note that day |
| `/week/2026-W30` | ISO week (Monday-start), day-divided |
| `/month/2026-07` | month, day-divided, paginated at 50 |
| `/year/2026` | **summary** — its months, not its notes |

Empty periods, malformed keys and unknown granularities all 404.

## Controls

State lives entirely in the URL, so every view is linkable and shareable.

| Param | Values | Effect |
|-------|--------|--------|
| `restacks` | `1` | folds in the 662 restacked notes, tinted and labelled with their source |
| `sort` | `desc` (default), `asc`, `top` | newest first / oldest first / most reactions first |
| `page` | integer | page within a period; clamps to the last page rather than rendering empty |

`sort=top` ranks notes by reactions inside a period, and ranks periods by total
reactions on index pages. Two deliberate consequences: day dividers are hidden
(ranked notes jump between dates, so dividers would repeat and mislead), and the
day/week index drops its year grouping (the point is one ranked list).

## Navigation

**Breadcrumbs** on every period page — `All days › 2026 › July › W30 › Jul 26` —
each segment linking to that period, plus a route back to the current
granularity's index.

Weeks deliberately get **no month ancestor**: an ISO week can straddle two
months, so any single answer would be wrong roughly half the time.

**Drill-down strips** list the child periods inline — a year's months, a month's
or week's days.

**Prev/next** skips empty periods and flips direction with the sort order.

## Design notes

### Why years are summaries

Period sizes are lopsided, which drives the whole design:

| Granularity | Periods | Median notes | Max |
|---|---|---|---|
| Day | 596 | 6 | 25 |
| Week | 96 | 37 | 91 |
| Month | 23 | 161 | 300 |
| Year | 3 | 1,168 | **1,828** |

A year page rendering 1,828 notes is a multi-megabyte document, and paginating
it at 50 gives ~37 pages of nothing useful. So a year is presented as a map of
its months instead. Pagination then only really matters for months.

### Why the data is a JSON import, not a database

The corpus is 1.9 MB and read-only — it changes only when you re-scrape. A
static import means the bundler ships the data; bucketing 3,694 notes in memory
beats a network round-trip to Postgres before its query even runs. A runtime
`readFileSync` was tried first and replaced: a cwd-relative read is not reliably
traced into a serverless bundle.

Revisit only if you want the site to update *without* a redeploy — and even then
the first answer is a cron job hitting a deploy hook, not a database. Rough line:
under ~50 MB and read-only, stay on the file.

### Rendering and caching

Everything is server-rendered; no corpus data reaches the client.

Because the pages read `searchParams`, **every route is dynamic** and Next sets
`Cache-Control: no-store`, which overrides anything declared in
`next.config.mjs`. An earlier `s-maxage` header there looked effective and did
nothing; it has been removed rather than left to mislead.

Making the site genuinely static would mean moving `restacks`/`sort`/`page` out
of the query string and into the URL path. That was judged not worth it at this
traffic — navigation quality mattered more.

### Deploying

```bash
npx vercel deploy --prod --yes
```

CLI upload, not a git integration: the corpus is gitignored, so a repo-connected
deploy would ship an app with no data. `.vercelignore` exists for the same
reason — without it Vercel falls back to `.gitignore` and strips
`data/notes.json`.

`scripts/build-data.mjs` falls back to the committed `data/notes.json` when
`../substack_notes_all.json` is absent, which is the case in a standalone
deploy.

To roll back: `npx vercel rollback <previous-deployment-url>`.
