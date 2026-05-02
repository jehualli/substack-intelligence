import urllib.request
import urllib.parse
import json
import time
import os
import sys

# Usage: python scrape_notes_api.py <user_id> <output_file>
# Set SUBSTACK_SESSION_COOKIE env var for authenticated access (required for full history).

if len(sys.argv) < 3:
    print("Usage: python scrape_notes_api.py <user_id> <output_file>")
    print("Example: python scrape_notes_api.py 273636371 /path/to/notes.json")
    sys.exit(1)

USER_ID = int(sys.argv[1])
OUTPUT = sys.argv[2]
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
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 20 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")

all_notes = {}
page = 1

data = fetch({"limit": 25})
next_cursor = data.get("nextCursor")
for item in data.get("items", []):
    if item.get("type") == "comment":
        c = item["comment"]
        all_notes[c["id"]] = {
            "id": c["id"],
            "date": c.get("date"),
            "body": c.get("body", "").strip(),
            "reactions": c.get("reaction_count", 0),
            "restacks": c.get("restacks", 0),
            "replies": c.get("children_count", 0),
        }

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
                all_notes[c["id"]] = {
                    "id": c["id"],
                    "date": c.get("date"),
                    "body": c.get("body", "").strip(),
                    "reactions": c.get("reaction_count", 0),
                    "restacks": c.get("restacks", 0),
                    "replies": c.get("children_count", 0),
                }
                new += 1
                if oldest is None or c["date"] < oldest:
                    oldest = c["date"]

    if new > 0:
        print(f"  Page {page}: +{new} (total: {len(all_notes)}, oldest: {oldest[:10]})")

result = sorted(all_notes.values(), key=lambda n: n["date"], reverse=True)

print(f"\n=== DONE: {len(result)} notes ===")
print(f"Range: {result[-1]['date'][:10]} → {result[0]['date'][:10]}")

with open(OUTPUT, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"Saved to {OUTPUT}")
