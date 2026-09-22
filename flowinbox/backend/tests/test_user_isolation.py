import pytest
from app.retrieval.embeddings import FastEmbedProvider
from app.vectorstore.chroma import ChromaVectorStore


@pytest.mark.asyncio
async def test_chroma_user_isolation():
    provider = FastEmbedProvider()
    store = ChromaVectorStore(provider)

    await store.add_documents(
        ids=["doc_u1", "doc_u2"],
        texts=["User 1 email thread", "User 2 confidential email"],
        metadatas=[{"user_id": "u1"}, {"user_id": "u2"}]
    )

    # Attempt cross-user access for user u1 trying to view u2
    results = await store.search("confidential", user_id="u1")
    assert all(r["metadata"]["user_id"] == "u1" for r in results)
    assert not any(r["id"] == "doc_u2" for r in results)
