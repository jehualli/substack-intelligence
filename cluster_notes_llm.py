import json
import urllib.request
import os
import sys

# Usage: python cluster_notes_llm.py [notes_file]
# Reads notes JSON (default: substack_notes_api.json), calls Claude to cluster them,
# writes substack_clusters.json.

NOTES_FILE = sys.argv[1] if len(sys.argv) > 1 else "substack_notes_api.json"
OUTPUT = "substack_clusters.json"

with open(NOTES_FILE) as f:
    notes = json.load(f)

valid_notes = [n for n in notes if n["body"].strip()]

notes_text = ""
for i, n in enumerate(valid_notes):
    notes_text += f'[{i}] ({n["date"][:10]}) {n["body"][:200].strip()}\n\n'

PROMPT = f"""Here are {len(valid_notes)} Substack notes from a single author.
Identify 6-8 recurring topic clusters. For each cluster:
- Give it a short descriptive name
- List the note indices that belong to it
- Write a 1-sentence description of the theme

Format as JSON like this:
{{
  "clusters": [
    {{
      "name": "Cluster Name",
      "description": "One sentence about this theme.",
      "note_indices": [0, 3, 7, ...]
    }},
    ...
  ]
}}

Notes:
{notes_text}

Return only valid JSON, no other text."""

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    print("No ANTHROPIC_API_KEY found. Set it and re-run.")
    sys.exit(1)

payload = json.dumps({
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 4096,
    "messages": [{"role": "user", "content": PROMPT}]
}).encode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=payload,
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    method="POST",
)

print("Calling Claude API for semantic clustering...")
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())

raw = result["content"][0]["text"].strip()
clusters = json.loads(raw)["clusters"]

print(f"\n=== {len(clusters)} TOPIC CLUSTERS ===\n")

output = []
for c in clusters:
    indices = c["note_indices"]
    cluster_notes = [valid_notes[i] for i in indices if i < len(valid_notes)]
    avg_reactions = sum(n["reactions"] for n in cluster_notes) / len(cluster_notes) if cluster_notes else 0
    avg_restacks = sum(n["restacks"] for n in cluster_notes) / len(cluster_notes) if cluster_notes else 0
    top_notes = sorted(cluster_notes, key=lambda n: n["reactions"], reverse=True)

    print(f"--- {c['name']} ({len(indices)} notes) | avg reactions: {avg_reactions:.1f} ---")
    print(f"{c['description']}")
    print("Top notes:")
    for n in top_notes[:3]:
        preview = n["body"].replace("\n", " ")[:130]
        print(f"  [{n['date'][:10]}] reactions:{n['reactions']} restacks:{n['restacks']} | {preview}")
    print()

    output.append({
        "name": c["name"],
        "description": c["description"],
        "size": len(indices),
        "avg_reactions": round(avg_reactions, 1),
        "avg_restacks": round(avg_restacks, 1),
        "notes": [dict(
            id=n["id"],
            date=n["date"][:10],
            reactions=n["reactions"],
            restacks=n["restacks"],
            body=n["body"],
        ) for n in top_notes],
    })

output.sort(key=lambda c: -c["size"])
with open(OUTPUT, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"Saved to {OUTPUT}")
