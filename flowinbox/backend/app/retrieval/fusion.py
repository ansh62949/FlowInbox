from typing import List, Dict, Any


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
    k: int = 60,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """Merge and rank vector and lexical search results using Reciprocal Rank Fusion (RRF)."""
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # RRF for dense vector results
    for rank, item in enumerate(dense_results):
        doc_id = str(item.get("id"))
        doc_map[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

    # RRF for lexical results
    for rank, item in enumerate(lexical_results):
        doc_id = str(item.get("id"))
        if doc_id not in doc_map:
            doc_map[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

    # Sort combined results by RRF score
    sorted_ids = sorted(scores.keys(), key=lambda doc_id: scores[doc_id], reverse=True)

    fused_results = []
    for doc_id in sorted_ids[:top_n]:
        res = doc_map[doc_id]
        res["score"] = scores[doc_id]
        fused_results.append(res)

    return fused_results
