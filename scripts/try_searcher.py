import sys

from labellens.retrieval.search import Searcher

s = Searcher()
query = " ".join(sys.argv[1:]) or "nutella"
for h in s.products(query):
    print(f"{h['score']:.3f}  {h['name']}  |  {h['brands']}  |  {h['code']}")
print()
for card in s.knowledge("hidden animal ingredients in vegan food", exclude_types=["additive"]):
    print(card["type"], "|", card["title"])
