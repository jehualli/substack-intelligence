# Substack Intelligence Pipeline

A multi-stage pipeline that scrapes a Substack author's notes, clusters them semantically using Claude, and generates a longform narrative profile.

## Pipeline

```
scrape_notes_api.py → substack_notes_api.json
        ↓
cluster_notes_llm.py → substack_clusters.json    (uses Claude Haiku)
        ↓
generate_story.py → substack_story.md             (uses Claude Sonnet)
```

There's also `cluster_notes_sklearn.py` as an LDA-based alternative to the Claude clustering step (no API key needed).

## Setup

No external dependencies for the main pipeline — uses Python stdlib only.

```bash
export ANTHROPIC_API_KEY=your_key_here

# For private profiles (get from browser DevTools → Application → Cookies → substack.sid):
export SUBSTACK_SESSION_COOKIE=your_cookie_here
```

## Usage

### 1. Scrape notes

```bash
python scrape_notes_api.py <user_id>
```

The `user_id` is the numeric ID in the Substack reader API. You can find it by inspecting network requests on a profile's notes page, or by checking the URL pattern `substack.com/api/v1/reader/feed/profile/<user_id>`.

Output: `substack_notes_api.json`

### 2. Cluster with Claude

```bash
python cluster_notes_llm.py
```

Calls Claude Haiku to identify 6-8 recurring topic clusters across all notes, returns structured JSON with engagement metrics per cluster.

Output: `substack_clusters.json`

### 3. Generate narrative

```bash
python generate_story.py
```

Calls Claude Sonnet to write a 500-700 word analytical profile of the author based on clusters and top-performing notes.

Output: `substack_story.md`

### Alternative: LDA clustering (no API key)

```bash
pip install scikit-learn numpy
python cluster_notes_sklearn.py
```

### API discovery tool

```bash
pip install playwright && playwright install chromium
python find_scroll_api.py <substack_handle>
```

Intercepts and logs all Substack API calls made during page load and scrolling — useful for reverse-engineering pagination.

## How it works

**Scraping:** Substack doesn't expose a public API for notes. This pipeline reverse-engineers the private `reader/feed/profile` endpoint, reconstructing the base64-encoded cursor format (timestamp + entity key + pinned keys + page number) needed for pagination.

**Clustering:** Rather than keyword matching, Claude reads all notes in a single prompt and identifies semantic themes — grouping posts by conceptual similarity rather than exact word overlap.

**Narrative generation:** Claude Sonnet synthesizes cluster data and top-performing posts into a coherent analytical profile, surfacing patterns in what resonates vs. what falls flat with the audience.
