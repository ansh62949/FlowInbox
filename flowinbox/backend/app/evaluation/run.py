import asyncio
import json
import uuid
from typing import Dict, Any, List
from app.agents.graph import build_flowinbox_graph


EVAL_BENCHMARK_SET = [
    {
        "id": "eval_01",
        "category": "recruiter-thread discovery",
        "query": "Find recruiters I contacted more than 5 days ago who haven't replied",
        "expected_intent": "recruiter_followup",
        "expected_tool": "search_emails"
    },
    {
        "id": "eval_02",
        "category": "interview-detail retrieval",
        "query": "Find my interview with XYZ tomorrow and prepare me for it",
        "expected_intent": "interview_prep",
        "expected_tool": "search_emails"
    },
    {
        "id": "eval_03",
        "category": "daily summary",
        "query": "Summarize everything important from today's emails",
        "expected_intent": "daily_digest",
        "expected_tool": "search_emails"
    },
    {
        "id": "eval_04",
        "category": "needs-reply detection",
        "query": "Find emails from recruiters that I haven't replied to",
        "expected_intent": "recruiter_followup",
        "expected_tool": "search_emails"
    },
    {
        "id": "eval_05",
        "category": "follow-up prep",
        "query": "Prepare a personalized follow-up draft for Priya at TechCorp",
        "expected_intent": "recruiter_followup",
        "expected_tool": "create_draft"
    },
    {
        "id": "eval_06",
        "category": "context-retrieval accuracy",
        "query": "What time is my interview scheduled for tomorrow?",
        "expected_intent": "interview_prep",
        "expected_tool": "get_events"
    }
]


def calculate_groundedness(final_state: Dict[str, Any]) -> float:
    """Compute dynamic groundedness score by checking strict traceability of response claims against retrieved context."""
    retrieved = final_state.get("retrieved_context", [])
    pending = final_state.get("pending_actions", [])
    response = final_state.get("final_response") or ""

    if not response and pending:
        # If action is pending, evaluate body text of pending draft payload
        response = " ".join([str(p.get("payload", {}).get("body", "")) for p in pending])

    if not response:
        return 0.0

    # Collect source tokens from retrieved context
    source_text = " ".join([str(item.get("snippet", "")) + " " + str(item.get("subject", "")) for item in retrieved]).lower()

    if not source_text.strip():
        return 0.0

    # Count response words grounded strictly in source text (Step 6 requirement: no keyword fallbacks!)
    resp_words = [w.lower() for w in response.split() if len(w) > 3]
    if not resp_words:
        return 1.0

    grounded_words = [w for w in resp_words if w in source_text]
    return round(len(grounded_words) / len(resp_words), 2)


async def run_full_evaluation():
    print("==================================================")
    print("      FlowInbox AI — Computed Evaluation Suite    ")
    print("==================================================")

    graph = build_flowinbox_graph()
    eval_user_id = str(uuid.uuid4())

    passed_count = 0
    total_evals = len(EVAL_BENCHMARK_SET)
    results = []

    for test in EVAL_BENCHMARK_SET:
        initial_state = {
            "user_id": eval_user_id,
            "request": test["query"],
            "intent": None,
            "plan": [],
            "messages": [{"role": "user", "content": test["query"]}],
            "tool_calls": [],
            "tool_results": [],
            "retrieved_context": [],
            "relevant_threads": [],
            "pending_actions": [],
            "approval_status": "none",
            "final_response": None,
            "errors": [],
            "task_status": "running"
        }

        # Actually invoke LangGraph agent
        final_state = await graph.ainvoke(initial_state)

        # Read actual classified intent
        actual_intent = final_state.get("intent")
        intent_match = (actual_intent == test["expected_intent"])

        # Read actual tools called
        tools_called = [tc.get("tool") for tc in final_state.get("tool_calls", [])]
        tool_match = test["expected_tool"] in tools_called

        # Dynamically compute groundedness and hallucination rate
        groundedness_score = calculate_groundedness(final_state)
        hallucination_rate = round(1.0 - groundedness_score, 2)

        # Both intent and tool match required for PASS
        is_pass = intent_match and tool_match
        if is_pass:
            passed_count += 1

        status = "PASSED" if is_pass else "FAILED"

        results.append({
            "id": test["id"],
            "category": test["category"],
            "query": test["query"],
            "expected_intent": test["expected_intent"],
            "actual_intent": actual_intent,
            "intent_match": intent_match,
            "expected_tool": test["expected_tool"],
            "actual_tools": tools_called,
            "tool_match": tool_match,
            "groundedness_score": groundedness_score,
            "hallucination_rate": hallucination_rate,
            "status": status
        })

        intent_check_str = "OK" if intent_match else "ERR"
        tool_check_str = "OK" if tool_match else "ERR"

        print(f"[{status}] {test['id']} - {test['category']}:")
        print(f"   Query: '{test['query']}'")
        print(f"   Intent (actual vs expected): '{actual_intent}' vs '{test['expected_intent']}' ({intent_check_str})")
        print(f"   Tools (actual vs expected): {tools_called} vs '{test['expected_tool']}' ({tool_check_str})")
        print(f"   Groundedness: {groundedness_score} | Hallucination Rate: {hallucination_rate}\n")

    accuracy = (passed_count / total_evals) * 100
    avg_groundedness = round(sum(r["groundedness_score"] for r in results) / total_evals, 2)
    avg_hallucination = round(sum(r["hallucination_rate"] for r in results) / total_evals, 2)

    report = {
        "total_tests": total_evals,
        "passed": passed_count,
        "accuracy_pct": accuracy,
        "mean_groundedness": avg_groundedness,
        "mean_hallucination_rate": avg_hallucination,
        "results": results
    }

    print("--------------------------------------------------")
    print(f"Computed Accuracy: {accuracy:.1f}% ({passed_count}/{total_evals})")
    print(f"Mean Groundedness: {avg_groundedness} | Mean Hallucination Rate: {avg_hallucination}")
    print("--------------------------------------------------\n")
    return report


if __name__ == "__main__":
    asyncio.run(run_full_evaluation())
