from typing import Dict, Any, List
import logging
import datetime
from langgraph.graph import StateGraph, END
from app.agents.state import FlowInboxState
from app.llm.manager import LLMManager
from app.approval.policy import ActionPolicyEngine
from app.tools.email_tools import search_emails_func, SearchEmailsInput, create_draft_func, CreateDraftInput
from app.tools.calendar_tools import get_events_func, GetEventsInput

logger = logging.getLogger("flowinbox.agents.graph")
llm_manager = LLMManager()


async def request_understanding_node(state: FlowInboxState) -> FlowInboxState:
    """Parse user natural language intent using live LLM call."""
    req = state["request"]
    prompt = (
        "Classify the following user request into exactly ONE of these intents:\n"
        "- interview_prep: queries asking about interview schedule, meeting times, or preparing for an upcoming interview.\n"
        "- recruiter_followup: queries asking to find recruiters to follow up with or draft follow-up emails.\n"
        "- daily_digest: queries asking to summarize today's emails or give an inbox overview.\n"
        "- general_query: any other request.\n\n"
        f"User Request: '{req}'\n"
        "Return ONLY the single intent keyword (interview_prep, recruiter_followup, daily_digest, or general_query) with no extra text."
    )

    intent = "general_query"
    try:
        llm_res = await llm_manager.generate([{"role": "user", "content": prompt}])
        raw_text = llm_res.get("content", "").strip().lower()
        logger.info(f"[RequestUnderstanding] Live LLM classified intent: '{raw_text}' (Provider: {llm_res.get('provider')})")

        for valid_intent in ["interview_prep", "recruiter_followup", "daily_digest", "general_query"]:
            if valid_intent in raw_text:
                intent = valid_intent
                break
    except Exception as e:
        logger.warning(f"[RequestUnderstanding] LLM call failed ({str(e)}). Using keyword fallback path.")
        req_lower = req.lower()
        if "interview" in req_lower or "prep" in req_lower or "time" in req_lower or "schedule" in req_lower:
            intent = "interview_prep"
        elif "recruiter" in req_lower or "follow" in req_lower:
            intent = "recruiter_followup"
        elif "summarize" in req_lower or "digest" in req_lower:
            intent = "daily_digest"

    state["intent"] = intent
    state["task_status"] = "running"
    return state


async def planner_node(state: FlowInboxState) -> FlowInboxState:
    """Generate multi-step execution plan."""
    intent = state["intent"]
    if intent == "recruiter_followup":
        plan = [
            "Search emails for recruiter communications",
            "Retrieve context and contact details",
            "Generate personalized follow-up draft using LLM",
            "Request human approval before sending"
        ]
    elif intent == "interview_prep":
        plan = [
            "Search Calendar for interview event details",
            "Retrieve related Gmail thread history",
            "Generate grounded interview brief using LLM"
        ]
    elif intent == "daily_digest":
        plan = [
            "Search today's emails",
            "Retrieve context",
            "Generate grounded daily summary using LLM"
        ]
    else:
        plan = ["Retrieve relevant emails", "Generate LLM response"]

    state["plan"] = plan
    return state


async def agent_tool_loop_node(state: FlowInboxState) -> FlowInboxState:
    """Execute tools and call LLM to dynamically generate responses/drafts from retrieved context with graceful fallback."""
    intent = state["intent"]
    user_id = state["user_id"]
    req = state["request"]

    if intent == "recruiter_followup":
        res = await search_emails_func(SearchEmailsInput(user_id=user_id, query=req, days_filter=5))
        state["tool_calls"].append({"tool": "search_emails", "input": {"query": req}})
        state["tool_results"].append({"tool_name": "search_emails", "result": res.data})
        state["retrieved_context"].extend(res.emails)

        context_str = "\n".join([f"- Sender: {e.get('sender')} | Subject: {e.get('subject')} | Body: {e.get('snippet')}" for e in res.emails])
        draft_prompt = (
            "Based on the following retrieved recruiter emails, draft a polite, professional follow-up email:\n"
            f"Retrieved Context:\n{context_str}\n\n"
            "Generate ONLY a draft email body without subject line or preamble."
        )

        try:
            llm_draft = await llm_manager.generate([{"role": "user", "content": draft_prompt}])
            draft_body = llm_draft.get("content", "").strip()
        except Exception as e:
            logger.warning(f"[AgentToolLoop] LLM call failed for draft generation: {str(e)}. Using fallback text.")
            state["errors"].append(f"LLM draft generation fallback: {str(e)}")
            draft_body = "Hi, following up on our previous conversation regarding the open position. Please let me know if you have any updates."

        to_email = res.emails[0].get("sender_email", "") if res.emails else ""
        subject_line = f"Re: {res.emails[0].get('subject', 'Position Follow-up')}" if res.emails else "Re: Follow-up"

        draft_res = await create_draft_func(CreateDraftInput(
            user_id=user_id,
            to_email=to_email,
            subject=subject_line,
            body=draft_body
        ))
        state["tool_calls"].append({"tool": "create_draft", "input": {"to_email": to_email}})
        state["tool_results"].append({"tool_name": "create_draft", "result": draft_res.data})

        state["pending_actions"].append({
            "action_type": "send_email",
            "payload": {
                "draft_id": draft_res.draft_id,
                "recipient": to_email,
                "subject": subject_line,
                "body": draft_body
            }
        })

    elif intent == "interview_prep":
        email_res = await search_emails_func(SearchEmailsInput(user_id=user_id, query=req))
        state["tool_calls"].append({"tool": "search_emails", "input": {"query": req}})
        state["tool_results"].append({"tool_name": "search_emails", "result": email_res.data})
        state["retrieved_context"].extend(email_res.emails)

        # Compute dynamic 'tomorrow' time window
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        tomorrow = now_utc + datetime.timedelta(days=1)
        start_iso = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_iso = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        event_res = await get_events_func(GetEventsInput(
            user_id=user_id,
            start_time=start_iso,
            end_time=end_iso
        ))
        state["tool_calls"].append({"tool": "get_events", "input": {"start_time": start_iso}})
        state["tool_results"].append({"tool_name": "get_events", "result": event_res.data})

        context_str = "\n".join([f"- Email: {e.get('subject')} | {e.get('snippet')}" for e in email_res.emails])
        context_str += "\n" + "\n".join([f"- Calendar Event: {ev.get('title')} at {ev.get('start_time')}" for ev in event_res.events])

        summary_prompt = (
            "Generate a concise, grounded interview preparation brief based strictly on the retrieved details below:\n"
            f"Retrieved Context:\n{context_str}\n\n"
            "User Request: " + req + "\n\n"
            "Formatting Rules:\n"
            "- Start with a clear header: '### Interview Preparation Brief'\n"
            "- Present key details as short bullet points with bold lead phrases (e.g. '- **Meeting Time**: ...')\n"
            "- Keep bullets short and scannable with spacing."
        )
        try:
            llm_prep = await llm_manager.generate([{"role": "user", "content": summary_prompt}])
            state["final_response"] = llm_prep.get("content", "").strip()
        except Exception as e:
            logger.warning(f"[AgentToolLoop] LLM call failed for interview brief: {str(e)}. Using fallback text.")
            state["errors"].append(f"LLM interview brief fallback: {str(e)}")
            state["final_response"] = f"Interview preparation details retrieved from email thread and calendar event ({start_iso})."

    elif intent == "daily_digest":
        res = await search_emails_func(SearchEmailsInput(user_id=user_id, query=req))
        state["tool_calls"].append({"tool": "search_emails", "input": {"query": req}})
        state["tool_results"].append({"tool_name": "search_emails", "result": res.data})
        state["retrieved_context"].extend(res.emails)

        frontend_url = settings.FRONTEND_URL.rstrip('/')
        context_str = "\n".join([f"- Subject: {e.get('subject')} | Sender: {e.get('sender')} | Snippet: {e.get('snippet')} | ID: {e.get('id')}" for e in res.emails])
        digest_prompt = (
            "Summarize the user's unread/recent inbox messages into an executive summary:\n"
            f"Retrieved Emails:\n{context_str}\n\n"
            "Formatting Rules:\n"
            "- Start with a clear header: '### 📥 Daily Inbox Digest'\n"
            "- Include an 'Overview' sentence summarizing overall inbox urgency and actionable status.\n"
            f"- List key actionable threads as bullet points formatted with markdown links: '[Subject Line]({frontend_url}/inbox?thread=ID)' — short 1-line description.\n"
            "- Keep response concise, grounded, and clean."
        )
        try:
            llm_digest = await llm_manager.generate([{"role": "user", "content": digest_prompt}])
            state["final_response"] = llm_digest.get("content", "").strip()
        except Exception as e:
            logger.error(f"[AgentToolLoop] LLM call failed for daily digest: {str(e)}", exc_info=True)
            state["errors"].append(f"LLM daily digest error: {str(e)}")
            state["final_response"] = f"Daily inbox summary: retrieved {len(res.emails)} relevant emails. (LLM Provider Error: {str(e)})"

    else:
        # general_query or fallback intent handler
        res = await search_emails_func(SearchEmailsInput(user_id=user_id, query=req))
        state["tool_calls"].append({"tool": "search_emails", "input": {"query": req}})
        state["tool_results"].append({"tool_name": "search_emails", "result": res.data})
        state["retrieved_context"].extend(res.emails)

        if not res.emails:
            prompt = (
                f"The user asked: '{req}'\n\n"
                "You searched their inbox, but found 0 relevant emails or matching documents.\n"
                "Respond directly and clearly stating that no matching emails or information were found in their inbox for this query."
            )
        else:
            context_str = "\n".join([
                f"- ID: {e.get('id')} | Sender: {e.get('sender')} | Subject: {e.get('subject')} | Snippet: {e.get('snippet')} | Date: {e.get('sent_at')}"
                for e in res.emails
            ])
            prompt = (
                f"Answer the user's question directly and thoroughly based strictly on the retrieved inbox context below.\n"
                f"User Question: '{req}'\n\n"
                f"Retrieved Inbox Context:\n{context_str}\n\n"
                "Formatting & Tone Rules:\n"
                "- Provide a clear, natural, and grounded answer referencing retrieved emails.\n"
                "- Use markdown bolding and list formatting for key items.\n"
                f"- Link important email threads using markdown format: '[Subject Line]({frontend_url}/inbox?thread=ID)'."
            )

        try:
            llm_res = await llm_manager.generate([{"role": "user", "content": prompt}])
            state["final_response"] = llm_res.get("content", "").strip()
        except Exception as e:
            logger.error(f"[AgentToolLoop] LLM call failed for general query: {str(e)}", exc_info=True)
            state["errors"].append(f"LLM general query error: {str(e)}")
            state["final_response"] = f"Searched inbox for '{req}' and found {len(res.emails)} matching emails. (LLM Provider Error: {str(e)})"

    return state


async def action_policy_node(state: FlowInboxState) -> FlowInboxState:
    """Evaluate proposed actions against policy engine."""
    if not state["pending_actions"]:
        state["approval_status"] = "none"
        return state

    for action in state["pending_actions"]:
        risk_level, allowed, requires_approval, reason = ActionPolicyEngine.evaluate_action(
            action["action_type"], action["payload"]
        )
        if requires_approval:
            state["approval_status"] = "pending"
            state["task_status"] = "waiting_approval"
            return state

    state["approval_status"] = "none"
    return state


def router_approval(state: FlowInboxState) -> str:
    """Route graph flow based on approval state."""
    if state["approval_status"] == "pending":
        return "human_approval"
    return "final_response"


async def human_approval_node(state: FlowInboxState) -> FlowInboxState:
    """Pause graph state machine when approval is required."""
    state["task_status"] = "waiting_approval"
    return state


async def final_response_node(state: FlowInboxState) -> FlowInboxState:
    """Format grounded final response when task completes."""
    if state["approval_status"] == "pending":
        state["task_status"] = "waiting_approval"
        return state

    if not state.get("final_response"):
        logger.warning(
            f"[FinalResponseNode] Safety fallback triggered! No final_response was set in state for intent '{state.get('intent')}'. "
            f"Context count: {len(state.get('retrieved_context', []))}, Pending actions: {len(state.get('pending_actions', []))}"
        )
        state["final_response"] = (
            f"Successfully executed workflow for intent '{state['intent']}'. "
            f"Found {len(state['retrieved_context'])} relevant context documents. "
            f"Generated {len(state['pending_actions'])} pending action items for your review."
        )
    state["task_status"] = "completed"
    return state


def build_flowinbox_graph():
    """Construct compiled LangGraph state graph."""
    workflow = StateGraph(FlowInboxState)

    workflow.add_node("request_understanding", request_understanding_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("agent_tool_loop", agent_tool_loop_node)
    workflow.add_node("action_policy", action_policy_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("final_response", final_response_node)

    workflow.set_entry_point("request_understanding")
    workflow.add_edge("request_understanding", "planner")
    workflow.add_edge("planner", "agent_tool_loop")
    workflow.add_edge("agent_tool_loop", "action_policy")

    workflow.add_conditional_edges(
        "action_policy",
        router_approval,
        {
            "human_approval": "human_approval",
            "final_response": "final_response"
        }
    )
    workflow.add_edge("human_approval", END)
    workflow.add_edge("final_response", END)

    return workflow.compile()
