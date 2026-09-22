# FlowInbox AI 🚀

> **Tagline:** "Your inbox, with an AI teammate."

FlowInbox AI is a production-grade, AI-native collaborative email workspace inspired by Upstream's UX. It connects directly to your Google account (Gmail & Google Calendar) to perform automated thread triage, grounded writing synthesis, team channel collaboration, human approval governance, and Model Context Protocol (MCP) server integration.

---

## 📸 Key Capabilities

1. **3 Primary Navigation Modes**: Global vertical rail strictly focused on ✨ **AI Chat**, ✉ **Inbox**, and **# Channels** with modal **Settings** overlay.
2. **Side-by-side Resizable AI Workspace**: Resizable Assistant panel (300px–600px width) offering real-time LangGraph agent execution, model switching, and voice input.
3. **Deep Email Thread Analysis**: One-click thread analysis extracting Intent, Sender context, Required action, Priority score, Sentiment, and Suggested reply strategy.
4. **Needs Reply & Follow Up Agents**: Automated engine that analyzes incoming emails to surface messages requiring response and schedules follow-up reminders.
5. **Team Channels & Internal Comments**: Shared channel workspaces and thread internal comments for real-time team collaboration with AI agent participants.
6. **Human Safety Approval Gate**: Consequential actions like sending emails or creating calendar events require explicit human sign-off before dispatching.
7. **Model Context Protocol (MCP)**: Native stdio and HTTP streamable endpoints allowing external agents (Claude Desktop, Cursor IDE) to query inbox tools.

---

## 🏗 System Architecture

- **Frontend:** React 18 + Vite + Tailwind CSS + Framer Motion + Lucide Icons (`flowinbox/frontend`)
- **Backend:** Python FastAPI + Async SQLAlchemy 2.0 + Alembic + Pydantic v2 (`flowinbox/backend`)
- **Agent Orchestration:** LangGraph StateGraph (`app/agents/graph.py`)
- **LLM Engine:** Groq (Primary tool caller) with Gemini (Fallback) (`app/llm/`)
- **Vector Memory & Hybrid RAG:** Dense Vector Embeddings + PostgreSQL FTS + Reciprocal Rank Fusion (`app/retrieval/`)
- **Human Approval Policy:** Policy engine managing approval requests for `send_email`, `create_calendar_event`, etc. (`app/approval/policy.py`)

---

## 🛠 Google OAuth & GCP Setup Sequence

To authenticate real Google accounts and synchronize live Gmail messages and Google Calendar events:

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a project** -> **New Project** and name it `FlowInbox AI`.

### Step 2: Enable Google APIs
Enable the following APIs under **APIs & Services > Library**:
- **Gmail API**
- **Google Calendar API**
- **Google People API**

### Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**.
2. Select **External** (or **Internal** if using Workspace).
3. Fill in App Name (`FlowInbox AI`), User support email, and Developer contact information.
4. Add Scopes:
   - `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/calendar.events`

### Step 4: Create OAuth 2.0 Client Credentials
1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Application type: **Web application**.
4. Set Authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/google/callback`
5. Copy your **Client ID** and **Client Secret**.

### Step 5: Configure Backend `.env`
Update `flowinbox/backend/.env`:
```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flowinbox
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

---

## ⚡ Quick Start & Development

### 1. Database & Backend Services
```bash
# Navigate to backend
cd flowinbox/backend

# Install Python dependencies
py -3 -m pip install -r requirements.txt

# Run database migrations
py -3 -m alembic upgrade head

# Launch Uvicorn dev server
py -3 -m uvicorn app.main:app --port 8000 --reload
```

### 2. Frontend Web Workspace
```bash
# Navigate to frontend
cd flowinbox/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Verification & Test Suite

Run the full suite of automated backend tests:
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

## 🔌 Model Context Protocol (MCP) Configuration

FlowInbox provides a native MCP server for external AI tools like Claude Desktop or Cursor IDE.

### Claude Desktop Integration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "flowinbox": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp_server"
      ],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/flowinbox",
        "GROQ_API_KEY": "your-groq-api-key"
      }
    }
  }
}
```

---

## 📄 License & Attribution

Built for production AI workflows. Inspired by Upstream product architecture.

