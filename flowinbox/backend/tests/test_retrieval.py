import pytest
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.embeddings import FastEmbedProvider
from app.vectorstore.qdrant import QdrantVectorStore


def test_reciprocal_rank_fusion():
    dense = [{"id": "doc1", "score": 0.9}, {"id": "doc2", "score": 0.8}]
    lexical = [{"id": "doc2", "score": 10.0}, {"id": "doc3", "score": 5.0}]
    fused = reciprocal_rank_fusion(dense, lexical, top_n=2)
    assert len(fused) == 2
    assert fused[0]["id"] == "doc2"  # doc2 ranks high in both list 1 and 2


@pytest.mark.asyncio
async def test_qdrant_vectorstore_user_scoping():
    provider = FastEmbedProvider()
    store = QdrantVectorStore(provider)

    await store.add_documents(
        ids=["userA_doc1", "userB_doc1"],
        texts=["User A private email content", "User B private email content"],
        metadatas=[{"user_id": "user_A"}, {"user_id": "user_B"}]
    )

    results_a = await store.search("private email", user_id="user_A")
    assert len(results_a) == 1
    assert results_a[0]["id"] == "userA_doc1"
