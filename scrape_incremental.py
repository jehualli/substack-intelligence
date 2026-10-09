"""Incremental fetch of GLO's Substack notes newer than what's already on disk.

Walks the profile feed cursor until it goes past the newest date already stored,
then merges into substack_notes_all/original/restacks.json.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_ID = 273636371
BASE_URL = f"https://substack.com/api/v1/reader/feed/profile/{USER_ID}"
REPO = "/Users/jehualli/substack-intelligence"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}
cookie = os.environ.get("SUBSTACK_SESSION_COOKIE", "")
if cookie:
    HEADERS["Cookie"] = f"substack.sid={cookie}"


def fetch(params, retries=5):
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 20 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"  Network error ({e}), retrying in {wait}s...")
            time.sleep(wait)
    raise Exception("Max retries exceeded")


def parse_note(c):
    return {
        "id": c["id"],
        "date": c.get("date"),
        "author_id": c.get("user_id"),
        "author_name": c.get("name", ""),
        "author_handle": c.get("handle", ""),
        "body": (c.get("body") or "").strip(),
        "reactions": c.get("reaction_count", 0),
        "restacks": c.get("restacks", 0),
        "replies": c.get("children_count", 0),
    }


existing = {n["id"]: n for n in json.load(open(f"{REPO}/substack_notes_all.json"))}
newest_known = max(n["date"] for n in existing.values())
print(f"On disk: {len(existing)} notes, newest {newest_known[:10]}")

fetched = {}
page = 0
cursor = None
# Keep paging a few pages past the cutoff — feed ordering is not strictly monotonic.
past_cutoff_pages = 0

while True:
    page += 1
    params = {"limit": 25}
    if cursor:
        params["cursor"] = cursor
    data = fetch(params)
    cursor = data.get("nextCursor")

    dates = []
    new = 0
    for item in data.get("items", []):
        if item.get("type") != "comment":
            continue
        c = item["comment"]
        if not c.get("date"):
            continue
        dates.append(c["date"])
        if c["id"] not in fetched:
            fetched[c["id"]] = parse_note(c)
            if c["id"] not in existing:
                new += 1

    oldest = min(dates) if dates else None
    print(f"  Page {page}: +{new} new (oldest on page: {oldest[:10] if oldest else 'n/a'})")

    if oldest and oldest <= newest_known:
        past_cutoff_pages += 1
        if past_cutoff_pages >= 3:
            break
    if not cursor:
        break
    if page > 200:
        print("  Safety stop at 200 pages")
        break
    time.sleep(1.2)

merged = dict(existing)
added = 0
for nid, note in fetched.items():
    if nid not in merged:
        added += 1
    merged[nid] = note  # refresh engagement counts on re-seen notes

all_sorted = sorted(merged.values(), key=lambda n: n["date"], reverse=True)
original = [n for n in all_sorted if n["author_id"] == USER_ID]
restacks = [n for n in all_sorted if n["author_id"] != USER_ID]

print(f"\n=== +{added} new | {len(all_sorted)} total | {len(original)} original | {len(restacks)} restacks ===")
print(f"  Range: {all_sorted[-1]['date'][:10]} -> {all_sorted[0]['date'][:10]}")

for path, dataset in [
    ("substack_notes_all.json", all_sorted),
    ("substack_notes_original.json", original),
    ("substack_notes_restacks.json", restacks),
]:
    with open(f"{REPO}/{path}", "w") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(dataset)} -> {path}")
