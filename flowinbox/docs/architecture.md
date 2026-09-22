# FlowInbox AI Architecture Documentation

## Core Workflow Loop
1. **User Input / Task Trigger**: User submits a query or natural language command.
2. **Intent Parsing & Planning**: Agent analyzes query and generates a step-by-step plan.
3. **Context Retrieval**: Hybrid search combining Postgres Full-Text Search (keyword) and Qdrant/Chroma (dense vector embeddings) with Reciprocal Rank Fusion (RRF).
4. **Tool Execution**: Agent dynamically selects and executes strongly typed tools.
5. **Human-in-the-Loop Approval Engine**: Actions classified by risk level:
   - READ: Auto-approved
   - LOW_RISK: Auto-approved
   - CONSEQUENTIAL (send email, create/update event): Pauses agent graph, creates approval record, waits for human decision in UI
   - DANGEROUS: Blocked/disabled
6. **Execution & Audit Trail**: Approved actions execute and emit structured audit log events.
