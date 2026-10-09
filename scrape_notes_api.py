import urllib.request
import urllib.parse
import json
import time
import os
import sys

# Usage: python scrape_notes_api.py <user_id> <output_all> <output_original> <output_restacks>
# Set SUBSTACK_SESSION_COOKIE env var for authenticated access (required for full history).
# Splits output into original notes (author == user_id) and restacks.

if len(sys.argv) < 5:
    print("Usage: python scrape_notes_api.py <user_id> <output_all> <output_original> <output_restacks>")
    print("Example: python scrape_notes_api.py 273636371 all.json original.json restacks.json")
    sys.exit(1)

USER_ID = int(sys.argv[1])
OUTPUT_ALL = sys.argv[2]
OUTPUT_ORIGINAL = sys.argv[3]
OUTPUT_RESTACKS = sys.argv[4]
BASE_URL = f"https://substack.com/api/v1/reader/feed/profile/{USER_ID}"

SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}
if SESSION_COOKIE:
    HEADERS["Cookie"] = f"substack.sid={SESSION_COOKIE}"

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
        "body": c.get("body", "").strip(),
        "reactions": c.get("reaction_count", 0),
        "restacks": c.get("restacks", 0),
        "replies": c.get("children_count", 0),
    }

all_notes = {}
page = 1

data = fetch({"limit": 25})
next_cursor = data.get("nextCursor")
for item in data.get("items", []):
    if item.get("type") == "comment":
        c = item["comment"]
        all_notes[c["id"]] = parse_note(c)

print(f"Page 1: {len(all_notes)} notes")

while next_cursor:
    page += 1
    time.sleep(1.2)

    data = fetch({"limit": 25, "cursor": next_cursor})
    next_cursor = data.get("nextCursor")

    new, oldest = 0, None
    for item in data.get("items", []):
        if item.get("type") == "comment":
            c = item["comment"]
            if c["id"] not in all_notes:
                all_notes[c["id"]] = parse_note(c)
                new += 1
                if oldest is None or c["date"] < oldest:
                    oldest = c["date"]

    if new > 0:
        print(f"  Page {page}: +{new} (total: {len(all_notes)}, oldest: {oldest[:10]})")

    if page % 50 == 0:
        with open(OUTPUT_ALL + ".checkpoint", "w") as f:
            json.dump(sorted(all_notes.values(), key=lambda n: n["date"], reverse=True), f, ensure_ascii=False)

def save_results():
    all_sorted = sorted(all_notes.values(), key=lambda n: n["date"], reverse=True)
    original = [n for n in all_sorted if n["author_id"] == USER_ID]
    restacks = [n for n in all_sorted if n["author_id"] != USER_ID]
    print(f"\n=== {len(all_sorted)} total | {len(original)} original | {len(restacks)} restacks ===")
    if all_sorted:
        print(f"  Range: {all_sorted[-1]['date'][:10]} → {all_sorted[0]['date'][:10]}")
    for path, dataset in [(OUTPUT_ALL, all_sorted), (OUTPUT_ORIGINAL, original), (OUTPUT_RESTACKS, restacks)]:
        with open(path, "w") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(dataset)} → {path}")

import atexit
atexit.register(save_results)
