import json
import urllib.request
import os
import sys

# Usage: python generate_story.py [notes_file] [clusters_file]
# Reads notes + clusters, generates a longform narrative profile using Claude Sonnet.

NOTES_FILE = sys.argv[1] if len(sys.argv) > 1 else "substack_notes_api.json"
CLUSTERS_FILE = sys.argv[2] if len(sys.argv) > 2 else "substack_clusters.json"
OUTPUT = "substack_story.md"

with open(NOTES_FILE) as f:
    notes = json.load(f)
with open(CLUSTERS_FILE) as f:
    clusters = json.load(f)

valid = [n for n in notes if n["body"].strip()]
top_notes = sorted(valid, key=lambda n: n["reactions"], reverse=True)[:25]

notes_sample = "\n\n".join(
    f'[reactions:{n["reactions"]} restacks:{n["restacks"]} | {n["date"][:10]}]\n{n["body"][:400]}'
    for n in top_notes
)

def cluster_label(c):
    if "name" in c:
        return f'{c["name"].upper()} ({c["size"]} notes, avg reactions:{c["avg_reactions"]}): {c["description"]}'
    else:
        terms = ", ".join(c.get("top_terms", [])[:6])
        return f'TOPIC {c["topic"]} ({c["size"]} notes, avg reactions:{c["avg_reactions"]}): top terms: {terms}'

cluster_summary = "\n".join(cluster_label(c) for c in clusters)

PROMPT = f"""You are a cultural analyst. Based on the following data from a Substack author's notes, write a sharp, engaging narrative profile — like something you'd read in a longform magazine piece.

TOPIC CLUSTERS FOUND:
{cluster_summary}

TOP NOTES BY ENGAGEMENT:
{notes_sample}

Write a 500-700 word narrative that:
1. Opens with a hook — who is this person and why are they interesting to analyze
2. Maps out their intellectual universe — what themes obsess them and how they connect
3. Analyzes what resonates with their audience vs what falls flat (use the reaction data)
4. Identifies any contradictions or tensions in their worldview
5. Closes with a synthesis — what does this tell us about the corner of the internet they inhabit

Write in a confident, analytical voice. No fluff. Be specific — quote or paraphrase actual notes."""

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    print("No ANTHROPIC_API_KEY found.")
    sys.exit(1)

payload = json.dumps({
    "model": "claude-sonnet-4-6",
    "max_tokens": 2048,
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

print("Generating narrative...\n")
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())

story = result["content"][0]["text"]
print(story)

with open(OUTPUT, "w") as f:
    f.write(story)
print(f"\n\nSaved to {OUTPUT}")
