import numpy as np
from labellens.embeddings.image import ClipImageEmbedder
from labellens.embeddings.sparse import Bm25SparseEmbedder
from labellens.embeddings.text import BgeTextEmbedder
from PIL import Image


def test_text_embedder_shapes_and_norm() -> None:
    emb = BgeTextEmbedder()
    vecs = emb.embed_documents(["chocolate", "water"])
    assert vecs.shape == (2, emb.dim)
    assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-3)
    assert emb.embed_query("chocolate").shape == (emb.dim,)


def test_bm25_sparse_embedder() -> None:
    emb = Bm25SparseEmbedder()
    doc_vecs = emb.embed_documents(["Dark chocolate bar", "Plain mineral water"])
    assert len(doc_vecs) == 2
    for vec in doc_vecs:
        assert len(vec.indices) == len(vec.values)
        assert len(vec.indices) > 0

    query_vec = emb.embed_query("chocolate")
    assert len(query_vec.indices) == len(query_vec.values)
    assert len(query_vec.indices) > 0


def test_clip_image_embedder_text_and_image() -> None:
    emb = ClipImageEmbedder()
    assert emb.dim == 512

    # Test text embedding
    text_vec = emb.embed_text("a jar of chocolate spread")
    assert text_vec.shape == (emb.dim,)
    assert np.isclose(np.linalg.norm(text_vec), 1.0, atol=1e-3)

    # Test image embedding
    dummy_img = Image.new("RGB", (224, 224), color=(255, 0, 0))
    img_vecs = emb.embed_images([dummy_img])
    assert img_vecs.shape == (1, emb.dim)
    assert np.allclose(np.linalg.norm(img_vecs, axis=1), 1.0, atol=1e-3)
