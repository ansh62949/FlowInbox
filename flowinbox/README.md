# FlowInbox AI 🚀

> **Tagline:** "Your inbox, with an AI teammate."

FlowInbox AI is a production-grade, AI-native collaborative email & productivity workspace inspired by Upstream's UX. It connects directly to your Google account (Gmail & Google Calendar) to perform automated thread triage, grounded writing synthesis, team channel collaboration, human-in-the-loop approval governance, and standard Model Context Protocol (MCP) server integration over Streamable HTTP.

---

## 🏗 System Architecture

```text
               ┌─────────────────────────────────┐
               │         Vercel Cloud            │
               │   React 18 + Vite (Frontend)    │
               └────────────────┬────────────────┘
                                │ HTTPS API / JSON
                                ▼
               ┌─────────────────────────────────┐
               │          Render Cloud           │
               │    FastAPI Application Server   │
               └────────┬───────┬───────┬────────┘
                        │       │       │
      ┌─────────────────┘       │       └─────────────────┐
      ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐         ┌─────────────────┐
│ PostgreSQL   │        │ Qdrant Cloud │         │ Google Cloud    │
│ Managed DB   │        │ Vector Store │         │ Gmail & Calendar│
└──────────────┘        └──────────────┘         └─────────────────┘
```

- **Frontend:** React 18 + Vite + Tailwind CSS + Framer Motion + Lucide Icons (`flowinbox/frontend`)
- **Backend API:** Python 3.11 + FastAPI + Async SQLAlchemy 2.0 + Alembic + Pydantic v2 (`flowinbox/backend`)
- **Agent Orchestration:** LangGraph StateGraph (`app/agents/graph.py`)
- **LLM Engine:** Groq (`llama-3.3-70b-versatile`) with Google Gemini (`gemini-1.5-flash`) fallback (`app/llm/`)
- **Vector Memory & Hybrid RAG:** FastEmbed Dense Vectors + PostgreSQL Full-Text Search + Reciprocal Rank Fusion (`app/retrieval/`)
- **Human Approval Engine:** Policy gate managing approval requests for consequential actions (`send_email`, `create_calendar_event`) (`app/approval/policy.py`)
- **Model Context Protocol:** Official MCP SDK (`mcp>=1.0.0`) Streamable HTTP transport mounted at `/mcp`

---

## 📸 Key Capabilities

1. **AI Chat & Collaborative Inbox**: Clean sidebar navigation for AI Assistant, Inbox tabs, Team Channels, and Settings.
2. **Deep Email Thread Triage**: Extract Intent, Sender context, Required action, Priority score, Sentiment, and Suggested reply strategy.
3. **Needs Reply & Follow Up Engines**: Automated classification surfacing actionable incoming messages requiring user response while filtering out newsletters, automated receipts, and promotional mail.
4. **Real Google Calendar Integration**: Sync live Google Calendar events using encrypted OAuth tokens and show matching email thread context.
5. **Team Workspaces & Invitation System**: Multi-tenant team memberships with tokenized invitation links and SHA-256 hashed token storage.
6. **Human Safety Approval Gate**: Mandatory human sign-off before sending emails or creating calendar events.
7. **Model Context Protocol (MCP)**: Streamable HTTP transport exposing 7 tools (`search_emails`, `get_thread`, `get_events`, `list_pending_approvals`, `create_draft`, `propose_send_email`, `propose_create_event`) authenticated via API Tokens (`fl_token_...`).

---

## 🔐 Environment Variables Matrix

| Variable | Description | Development Default | Production Required |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Application mode | `development` | `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` | Yes (Render Postgres) |
| `REDIS_URL` | Redis cache connection string | `redis://localhost:6379/0` | Yes |
| `QDRANT_URL` | Qdrant Vector database endpoint | `http://localhost:6333` | Yes (Qdrant Cloud) |
| `GROQ_API_KEY` | Groq LLM API Key | `""` | Yes |
| `GROQ_MODEL` | Groq Catalog Model ID | `llama-3.3-70b-versatile` | `llama-3.3-70b-versatile` |
| `GEMINI_API_KEY` | Google Gemini API Key | `""` | Yes |
| `GEMINI_MODEL` | Gemini Catalog Model ID | `gemini-1.5-flash` | `gemini-1.5-flash` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | `""` | Yes |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | `""` | Yes |
| `GOOGLE_REDIRECT_URI` | Google OAuth Callback URL | `http://localhost:8000/api/v1/auth/google/callback` | `https://your-api.onrender.com/api/v1/auth/google/callback` |
| `ENABLE_GMAIL_SYNC` | Enable background sync loop | `true` | `true` |
| `JWT_SECRET` | Secret key for JWT signing | `super_secret_jwt_key` | Yes (256-bit random string) |
| `OAUTH_TOKEN_ENCRYPTION_KEY` | Fernet key for token encryption | `32_byte_key_here` | Yes (32-byte base64 key) |
| `FRONTEND_URL` | Frontend application origin | `http://localhost:8080` | `https://your-app.vercel.app` |

---

## 🛠 Google OAuth & GCP Setup Sequence

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named **FlowInbox AI**.
3. Enable **Gmail API**, **Google Calendar API**, and **Google People API**.
4. Configure **OAuth consent screen** with scopes:
   - `openid`, `email`, `profile`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events`
5. Create **OAuth 2.0 Client Credentials** (Web Application).
6. Add Authorized Redirect URIs:
   - Development: `http://localhost:8000/api/v1/auth/google/callback`
   - Production: `https://your-api.onrender.com/api/v1/auth/google/callback`

---

## 🔌 Model Context Protocol (MCP) Setup

FlowInbox implements standard Streamable HTTP MCP server mounted at `/mcp` (`http://localhost:8000/mcp`).

### Registering Tools & Authentication
- **Endpoint**: `http://localhost:8000/mcp`
- **Authentication**: Pass header `Authorization: Bearer <fl_token_...>` or query parameter `?token=<fl_token_...>`.
- **Tools Supported**:
  1. `search_emails`
  2. `get_thread`
  3. `get_events`
  4. `list_pending_approvals`
  5. `create_draft`
  6. `propose_send_email` (Approval gated)
  7. `propose_create_event` (Approval gated)

---

## ⚡ Local Quick Start

### 1. Backend Service
```bash
cd flowinbox/backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Application
```bash
cd flowinbox/frontend
npm install
npm run dev
```

---

## 🌐 Production Deployment (Render + Vercel)

### 1. Render Backend Web Service
1. Connect GitHub repository to Render.
2. Select Root Directory: `flowinbox/backend`.
3. Runtime: **Docker** (Builds using `flowinbox/backend/Dockerfile`).
4. Set Environment Variables in Render Dashboard (`DATABASE_URL`, `GROQ_API_KEY`, `GOOGLE_CLIENT_ID`, etc.).

### 2. Vercel Frontend SPA
1. Connect GitHub repository to Vercel.
2. Select Root Directory: `flowinbox/frontend`.
3. Framework Preset: **Vite**.
4. Set Environment Variable: `VITE_API_BASE_URL=https://your-api.onrender.com/api/v1`.

---

## 📄 License & Security

Built with privacy and human safety governance. All OAuth tokens encrypted at rest via Fernet AES-256.
