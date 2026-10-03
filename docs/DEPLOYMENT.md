# FlowInbox AI — Production Deployment Guide 🚀

This guide covers deploying **FlowInbox AI** using **Render** (Single-Service Full-Stack Docker container) and **Vercel** (Decoupled React Frontend + API backend).

---

## 🌐 Live Production Environments

- **Single-Service Full-Stack Container (Render):** [https://flowinbox-f93i.onrender.com](https://flowinbox-f93i.onrender.com)
- **Decoupled Frontend (Vercel):** [https://flow-inbox.vercel.app](https://flow-inbox.vercel.app)
- **OpenAPI Documentation:** [https://flowinbox-f93i.onrender.com/docs](https://flowinbox-f93i.onrender.com/docs)

---

## 🔑 Environment Variables Checklist

Ensure the following environment variables are set in your production environment dashboard (Render / Vercel):

### Backend Environment Variables (Render / Cloud Host)

| Variable Name | Required | Example / Description |
| :--- | :---: | :--- |
| `ENVIRONMENT` | Yes | `production` |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:password@host:5432/flowinbox_db` |
| `REDIS_URL` | Yes | `redis://default:password@host:6379/0` |
| `QDRANT_URL` | Yes | `http://qdrant:6333` or Qdrant Cloud URL |
| `GROQ_API_KEY` | Yes | Real Groq API key (`gsk_...`) |
| `GEMINI_API_KEY` | Yes | Real Gemini API key (`AIza...`) |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth Client ID (`...apps.googleusercontent.com`) |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth Client Secret (`GOCSPX-...`) |
| `JWT_SECRET` | Yes | Cryptographically secure secret string for session tokens |
| `OAUTH_TOKEN_ENCRYPTION_KEY` | Yes | 32-character secret key for AES-GCM token encryption |
| `FRONTEND_URL` | Yes | `https://flow-inbox.vercel.app` or `https://flowinbox-f93i.onrender.com` |

### Frontend Environment Variables (Vercel)

| Variable Name | Required | Example / Description |
| :--- | :---: | :--- |
| `VITE_API_BASE_URL` | Optional | `https://flowinbox-f93i.onrender.com` (Leave blank if same-origin) |

---

## 🚀 Deployment Option 1: Render (Full-Stack Docker Web Service)

Render builds and runs the container using [`flowinbox/backend/Dockerfile`](file:///c:/Users/satam/OneDrive/Desktop/ai-engineering-bootcamp-prerequisites-1/flowinbox/backend/Dockerfile). FastAPI serves the built React SPA frontend (`static/`) alongside backend API endpoints (`/api/v1`).

### Steps to Deploy on Render:
1. Log into **[Render Dashboard](https://dashboard.render.com)**.
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository (`ansh62949/FlowInbox`).
4. Set the build properties:
   - **Name:** `FlowInbox`
   - **Region:** Choose closest region (e.g. Oregon / Singapore)
   - **Branch:** `main`
   - **Root Directory:** `flowinbox/backend`
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `Dockerfile`
5. Add required environment variables under the **Environment** tab.
6. Click **Create Web Service**.

> **Note on Migrations:** The backend [`docker-entrypoint.sh`](file:///c:/Users/satam/OneDrive/Desktop/ai-engineering-bootcamp-prerequisites-1/flowinbox/backend/docker-entrypoint.sh) automatically runs `alembic upgrade head` before starting the server process.

---

## ⚡ Deployment Option 2: Vercel (Decoupled Frontend React SPA)

Host the React frontend on Vercel while pointing to your Render backend API.

### Steps to Deploy on Vercel:
1. Log into **[Vercel Dashboard](https://vercel.com)**.
2. Click **Add New...** → **Project**.
3. Import repository `ansh62949/FlowInbox`.
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `flowinbox/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://flowinbox-f93i.onrender.com`
6. Click **Deploy**.

---

## 🐳 Deployment Option 3: Local Docker Compose

To run the entire microservices stack (PostgreSQL, Redis, Qdrant, FastAPI Backend, React Frontend) locally:

```bash
cd flowinbox
docker compose up --build
```

Access local endpoints:
- **Frontend SPA:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`

---

## 🧪 Pre-Deployment Verification Command

Run the automated CI schema validator to verify database migrations coverage before pushing:

```bash
cd flowinbox/backend
py scripts/check_schema_migrations.py
py -m pytest tests/
```
