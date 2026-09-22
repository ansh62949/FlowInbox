# FlowInbox AI 🚀

> **FlowInbox AI** is an AI-native workspace where people, teams, and autonomous AI agents collaborate together on email communications, thread triage, calendar scheduling, and workflow automation.

---

## 🏗 System Architecture

```text
                      +---------------------------------------+
                      |          React 18 + Vite Web          |
                      |       (Tailwind CSS, Nginx Proxy)     |
                      +---------------------------------------+
                                          |
                                          v (HTTP / REST / SSE)
                      +---------------------------------------+
                      |         FastAPI Async Backend         |
                      |   (LangGraph Agent, Async SQLAlchemy) |
                      +---------------------------------------+
                               /          |          \
                              /           |           \
                             v            v            v
                +-----------------+  +---------+  +-----------------+
                |   PostgreSQL    |  |  Redis  |  |  Qdrant Vector  |
                | (Relational DB) |  | (Cache) |  |   (Hybrid RAG)  |
                +-----------------+  +---------+  +-----------------+
```

---

## 🛠 Tech Stack

* **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion, Lucide Icons
* **Backend**: Python 3.11, FastAPI, Async SQLAlchemy 2.0, Alembic, Pydantic v2
* **Agent Orchestration**: LangGraph StateGraph, Model Context Protocol (MCP)
* **LLM Engine & Routing**: Groq (`llama-3.3-70b-versatile`) primary tool caller, Google Gemini fallback
* **Vector Store & RAG**: Qdrant Vector Store, Dense Vector Embeddings + PostgreSQL Full-Text Search (FTS) merged via Reciprocal Rank Fusion (RRF)
* **Infrastructure**: Docker Compose, Kubernetes (`kind`), GitHub Actions CI/CD with GitHub Container Registry (GHCR)

---

## ✨ Key Features

1. **Google Workspace Sync**: Direct OAuth 2.0 connection to live Gmail threads and Google Calendar events.
2. **Deep Email Analysis & Grounded Drafting**: One-click synthesis of intent, sender context, sentiment, urgency scores, and grounded reply options.
3. **Human-in-the-Loop Safety Gate**: Consequential actions (`send_email`, `create_calendar_event`) generate a pending approval request requiring explicit human sign-off before dispatching.
4. **Model Context Protocol (MCP)**: Native stdio and HTTP SSE endpoints allowing external tools (Claude Desktop, Cursor IDE) to query inbox tools directly.
5. **Team Channels & Thread Collaboration**: Shared workspace channels and thread-level comments for real-time human and AI agent collaboration.
6. **Autonomous Background Engines**: `Needs Reply Engine` and `Followup Engine` for automated message triage and reminder tracking.

---

## ⚡ Quick Start & Development

### 1. Database & Backend Services
```bash
# Navigate to backend directory
cd flowinbox/backend

# Install Python dependencies
py -3 -m pip install -r requirements.txt

# Run database migrations
py -3 -m alembic upgrade head

# Start Uvicorn development server
py -3 -m uvicorn app.main:app --port 8000 --reload
```

### 2. Frontend Application
```bash
# Navigate to frontend directory
cd flowinbox/frontend

# Install dependencies
npm install

# Launch Vite development server
npm run dev
```
Open `http://localhost:3000` in your browser.

### 3. Docker Compose (Full Stack)
```bash
cd flowinbox
docker compose up --build
```

---

## 🧪 Verification & Testing

Run the full automated backend test suite:
```bash
cd flowinbox/backend
py -3 -m pytest tests/
```

Run frontend build verification:
```bash
cd flowinbox/frontend
npm run build
```

---

## ☸️ Kubernetes Deployment

FlowInbox AI includes complete, production-aligned Kubernetes manifests designed for local development on `kind` or cloud clusters:
- Namespace, ConfigMaps, Secret templates
- PostgreSQL & Qdrant PersistentVolumeClaims (PVC)
- Deployments with Startup, Liveness, and Readiness probes
- Nginx Ingress routing

See the dedicated **[Kubernetes Deployment Guide](k8s/README.md)** for step-by-step cluster setup instructions.

---

## 🔄 CI/CD Pipeline

Automated workflows are managed via GitHub Actions:
- **[CI (`.github/workflows/ci.yml`)](.github/workflows/ci.yml)**: Triggers on Pull Requests and pushes to `main`. Executes backend `pytest` suite and frontend build checks.
- **[CD (`.github/workflows/cd.yml`)](.github/workflows/cd.yml)**: Triggers on merge to `main`. Authenticates to GitHub Container Registry (GHCR), builds Docker images tagged with Git commit SHA and `latest`, and pushes to `ghcr.io`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
