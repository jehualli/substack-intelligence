import json, collections, re

U = 273636371
d = json.load(open("substack_notes_all.json"))
orig = sorted([n for n in d if n["author_id"] == U], key=lambda x: x["date"])

TARGETS = {
    "Mainstream right / grifters": r"jordan peterson|ben shapiro|charlie kirk|bet[- ]david|nick fuentes|andrew tate|jack murphy|matt walsh|tim pool|cuckservative|conservatard|cuckcervative|controlled opposition|mainstream conservative|conservaslop|rightoid|woke right|daily wire|prager|crowder",
    "Liberal women / feminism": r"liberal women|white wom|feminist|foid|\bfoids\b|shitlib wom|karen|girlboss|onlyfans|\bslut|hypergam|mommies|that girl|metoo|thot",
    "Boomers": r"boomer",
    "Jews / Zionism": r"\bjew|zionis|semit|israel|isreal|talmud|rothschild|masonic|freemason|khazar",
    "Immigration / H1B / Indians": r"h1b|h-1b|immigrant|migrant|indian|pajeet|jeet|visa|open border|great replacement|third world",
    "Globalists / capital / billionaires": r"globalist|billionaire|ruling class|zio capital|blackrock|wef|davos|federal reserve|agenda 2030|bankers|financializ|capital needs",
    "Normies / bugmen / NPCs": r"\bnormie|normtard|bugman|bugmen|\bnpc\b|goyim|goycattle|midwit|w2 employ|cubicle|wagie",
    "Leftists / liberals (generic)": r"leftoid|libtard|\bliberals\b|\bliberal \b|shitlib|marxist|communist|progressive|woke\b|dei\b|critical race",
    "State / surveillance / institutions": r"\bfbi\b|\bcia\b|\bfed\b|feds\b|surveillance|chat control|flock camera|digital id|police|government|public education|university|the eu\b|european union|censor",
    "Food industry / GoySlop": r"goyslop|goy slop|seed oil|glycosulphate|glyphosate|canola|processed food|slopified|normie slop|goysnack",
    "Big Tech / AI": r"\bai\b|openai|anthropic|chatgpt|sam altman|\bzuck|silicon valley|algorithm|vibe cod",
}
COMPILED = {k: re.compile(v, re.I) for k, v in TARGETS.items()}

months = collections.defaultdict(lambda: collections.Counter())
month_n = collections.Counter()
for n in orig:
    m = n["date"][:7]
    month_n[m] += 1
    b = n["body"]
    for k, rx in COMPILED.items():
        if rx.search(b):
            months[m][k] += 1

allm = sorted(months)
print(f"{'month':<9}{'notes':>6}  top targets (share of that month's notes)")
for m in allm:
    tot = month_n[m]
    top = months[m].most_common(4)
    s = "  ".join(f"{k.split(' /')[0]} {c/tot*100:.0f}%" for k, c in top)
    print(f"{m:<9}{tot:>6}  {s}")

print("\n=== per-target monthly share matrix (%) ===")
keys = list(TARGETS)
print(f"{'target':<34}" + "".join(f"{m[2:]:>7}" for m in allm))
for k in keys:
    print(f"{k:<34}" + "".join(f"{months[m][k]/month_n[m]*100:>7.0f}" for m in allm))
