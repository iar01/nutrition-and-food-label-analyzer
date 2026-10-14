import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

docs = [
    "Dark chocolate bar 70% cocoa, sugar, cocoa butter",
    "Milk chocolate hazelnut spread with palm oil",
    "Plain sparkling mineral water",
    "Wheat flour tortilla wraps",
]
queries = ["chocolate spread", "water", "gluten free bread"]

doc_vecs = model.encode(docs, normalize_embeddings=True)
print("vector shape:", doc_vecs.shape)  # (4, 384)
print("length of first vector:", np.linalg.norm(doc_vecs[0]))  # about 1.0

for q in queries:
    q_vec = model.encode(q, normalize_embeddings=True)
    scores = doc_vecs @ q_vec  # dot product == cosine because normalized
    best = int(np.argmax(scores))
    print(f"\nquery: {q!r}")
    for d, s in sorted(zip(docs, scores, strict=False), key=lambda x: -x[1]):
        print(f"  {s:.3f}  {d}")
