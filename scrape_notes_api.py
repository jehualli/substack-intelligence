import urllib.request
import urllib.parse
import json
import base64
import time
import os
import sys
from datetime import datetime, timezone

# Usage: python scrape_notes_api.py <user_id>
# Get the user_id from the Substack profile URL or network tab.
# Set SUBSTACK_SESSION_COOKIE env var for private profiles.

if len(sys.argv) < 2:
    print("Usage: python scrape_notes_api.py <user_id>")
    print("Example: python scrape_notes_api.py 273636371")
    sys.exit(1)

USER_ID = int(sys.argv[1])
LIMIT = 25
BASE_URL = f"https://substack.com/api/v1/reader/feed/profile/{USER_ID}"
OUTPUT = "substack_notes_api.json"

SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}
if SESSION_COOKIE:
    HEADERS["Cookie"] = f"substack.sid={SESSION_COOKIE}"

def make_cursor(before_timestamp, entity_key, context_timestamp, pinned_entity_keys, page_number):
    obj = {
        "before_timestamp": before_timestamp,
        "entity_key": entity_key,
        "pinned_entity_keys": pinned_entity_keys,
        "context_timestamp": context_timestamp,
        "secondary_context_timestamp": None,
        "prepended_post_ids": None,
        "page_number": page_number,
    }
    return base64.b64encode(json.dumps(obj).encode()).decode()

def fetch_page(params):
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def extract_notes(data):
    notes = []
    pinned_keys = []
    for item in data.get("items", []):
        if item.get("type") in ("post",):
            post = item.get("post", {})
            if post:
                pinned_keys.append(f"p-{post.get('id')}")
        if item.get("type") == "comment":
            c = item.get("comment", {})
            nid = c.get("id")
            if nid:
                notes.append({
                    "id": nid,
                    "entity_key": f"c-{nid}",
                    "date": c.get("date"),
                    "context_timestamp": item.get("context", {}).get("timestamp", c.get("date")),
                    "body": c.get("body", "").strip(),
                    "reactions": c.get("reaction_count", 0),
                    "restacks": c.get("restacks", 0),
                    "replies": c.get("children_count", 0),
                })
    return notes, pinned_keys

all_notes = []
seen_ids = set()

print("Fetching page 1...")
before_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
data = fetch_page({"limit": LIMIT})
notes, pinned_keys = extract_notes(data)
for n in notes:
    if n["id"] not in seen_ids:
        seen_ids.add(n["id"])
        all_notes.append(n)
print(f"  Got {len(notes)} items (total: {len(all_notes)}), pinned: {pinned_keys}")

page = 1
while notes:
    last = min(notes, key=lambda n: n["date"])
    cursor = make_cursor(
        before_timestamp=before_timestamp,
        entity_key=last["entity_key"],
        context_timestamp=last["context_timestamp"],
        pinned_entity_keys=pinned_keys,
        page_number=page - 1,
    )

    page += 1
    print(f"Fetching page {page} (last={last['entity_key']}, page_number={page-2})...")
    try:
        data = fetch_page({"limit": LIMIT, "cursor": cursor})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Rate limited, waiting 5s...")
            time.sleep(5)
            data = fetch_page({"limit": LIMIT, "cursor": cursor})
        else:
            print(f"  HTTP error {e.code}: {e}")
            break

    notes, new_pinned = extract_notes(data)
    if new_pinned:
        pinned_keys = new_pinned

    new_notes = [n for n in notes if n["id"] not in seen_ids]
    if not new_notes:
        print("  No new notes — done.")
        break

    for n in new_notes:
        seen_ids.add(n["id"])
        all_notes.append(n)

    print(f"  +{len(new_notes)} new notes (total: {len(all_notes)})")
    time.sleep(0.5)

all_notes.sort(key=lambda n: n["date"], reverse=True)

for n in all_notes:
    n.pop("entity_key", None)
    n.pop("context_timestamp", None)

print(f"\n=== DONE: {len(all_notes)} total notes ===")
with open(OUTPUT, "w") as f:
    json.dump(all_notes, f, indent=2, ensure_ascii=False)
print(f"Saved to {OUTPUT}")

print("\nAll notes:")
for n in all_notes:
    print(f"  [{n['date'][:10]}] ❤{n['reactions']} 🔁{n['restacks']} | {n['body'][:100]}")
