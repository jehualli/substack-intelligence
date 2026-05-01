import json
import sys
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Usage: python cluster_notes_sklearn.py [notes_file]
# Alternative to cluster_notes_llm.py — uses LDA (no API key needed).

NOTES_FILE = sys.argv[1] if len(sys.argv) > 1 else "substack_notes_api.json"
OUTPUT = "substack_clusters.json"

with open(NOTES_FILE) as f:
    notes = json.load(f)

valid_notes = [n for n in notes if n["body"].strip()]
texts = [n["body"].strip() for n in valid_notes]
print(f"Notes with content: {len(texts)} / {len(notes)}")

stopwords = set("""
a about above after again against all am an and any are as at be because been before being below
between both but by can cannot could did do does doing don down during each few for from further
get got had has have having he her here hers herself him himself his how i if in into is it its
itself just let me more most my myself no nor not of off on once only or other our ours ourselves
out over own same she should so some such than that the their theirs them themselves then there
these they this those through to too under until up very was we were what when where which while
who whom why will with would you your yours yourself yourselves
also just like get know don t can t won t i m re ve ll s going one think really want need
people every time make sure even back still well would could said right
""".split())

vectorizer = CountVectorizer(
    max_features=500,
    stop_words=list(stopwords),
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.90,
    token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b',
)
X = vectorizer.fit_transform(texts)
feature_names = vectorizer.get_feature_names_out()
print(f"Vocabulary size: {X.shape[1]} terms")

print("\nFitting LDA models...")
results = {}
for n_topics in range(5, 11):
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=30,
        learning_method="batch",
    )
    lda.fit(X)
    perplexity = lda.perplexity(X)
    results[n_topics] = (lda, perplexity)
    print(f"  n_topics={n_topics}: perplexity={perplexity:.1f}")

perplexities = [results[k][1] for k in range(5, 11)]
drops = [perplexities[i] - perplexities[i+1] for i in range(len(perplexities)-1)]
best_k = 5 + drops.index(max(drops)) + 1
print(f"\nSelected n_topics={best_k}")

lda, _ = results[best_k]
doc_topics = lda.transform(X)
topic_assignments = doc_topics.argmax(axis=1)

def top_terms(topic_idx, n=10):
    top_indices = lda.components_[topic_idx].argsort()[-n:][::-1]
    return [feature_names[i] for i in top_indices]

print("\n" + "="*70)
print(f"TOPIC CLUSTERS (LDA, {best_k} topics)")
print("="*70)

topic_data = []
for topic_idx in range(best_k):
    doc_indices = [i for i, t in enumerate(topic_assignments) if t == topic_idx]
    terms = top_terms(topic_idx)
    cluster_notes = [valid_notes[i] for i in doc_indices]
    avg_reactions = np.mean([n["reactions"] for n in cluster_notes]) if cluster_notes else 0
    avg_restacks = np.mean([n["restacks"] for n in cluster_notes]) if cluster_notes else 0
    top_by_reactions = sorted(cluster_notes, key=lambda n: n["reactions"], reverse=True)

    topic_data.append({
        "topic": topic_idx + 1,
        "size": len(doc_indices),
        "top_terms": terms,
        "avg_reactions": round(float(avg_reactions), 1),
        "avg_restacks": round(float(avg_restacks), 1),
        "notes": [dict(
            id=n["id"],
            date=n["date"][:10],
            reactions=n["reactions"],
            restacks=n["restacks"],
            body=n["body"],
        ) for n in top_by_reactions],
    })

topic_data.sort(key=lambda t: -t["size"])

for t in topic_data:
    print(f"\n--- Topic {t['topic']} ({t['size']} notes) | avg reactions: {t['avg_reactions']} ---")
    print(f"Terms: {', '.join(t['top_terms'])}")
    print("Top notes by reactions:")
    for n in t["notes"][:4]:
        preview = n["body"].replace("\n", " ")[:130]
        print(f"  [{n['date']}] reactions:{n['reactions']} restacks:{n['restacks']} | {preview}")

with open(OUTPUT, "w") as f:
    json.dump(topic_data, f, indent=2, ensure_ascii=False)
print(f"\n\nSaved to {OUTPUT}")
