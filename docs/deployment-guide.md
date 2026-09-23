# FlowInbox AI — Production Deployment Guide

## 1. Backend Deployment on Render (FastAPI Web Service)

1. Sign in to [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Connect your GitHub repository: `https://github.com/ansh62949/FlowInbox`.
3. Configure the service:
   - **Name:** `flowinbox-backend`
   - **Root Directory:** `flowinbox/backend`
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `./Dockerfile`
   - **Health Check Path:** `/api/v1/health`
4. Set the following **Environment Variables**:

| Variable Key | Required Value / Description |
| :--- | :--- |
| `GROQ_API_KEY` | Your real Groq API key (`gsk_...`) |
| `GEMINI_API_KEY` | Your real Google Gemini API key |
| `SECRET_KEY` | Random 32-byte hex string for JWT token signatures |
| `FRONTEND_URL` | Your Vercel frontend URL (e.g. `https://flowinbox.vercel.app`) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./flowinbox.db` |
| `ENABLE_GMAIL_SYNC` | `true` |
| `DEFAULT_LLM_PROVIDER` | `groq` |
| `DEFAULT_GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `DEFAULT_GEMINI_MODEL` | `gemini-1.5-flash` |

5. Click **Create Web Service**. Note your active backend URL (e.g. `https://flowinbox-backend.onrender.com`).

---

## 2. Frontend Deployment on Vercel (Vite React SPA)

1. Sign in to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New...** → **Project**.
2. Import repository `ansh62949/FlowInbox`.
3. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `flowinbox/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Set the following **Environment Variable**:

| Variable Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://flowinbox-backend.onrender.com/api/v1` |

5. Click **Deploy**. Vercel will build and host your production frontend.

---

## 3. GitHub Actions Continuous Deployment Integration (Optional)

1. Copy the **Deploy Hook URL** from Render Service Settings.
2. Copy the **Deploy Hook URL** from Vercel Project Settings.
3. In your GitHub Repository (`ansh62949/FlowInbox`), go to **Settings** → **Secrets and variables** → **Actions** and add:
   - `RENDER_DEPLOY_HOOK_URL`
   - `VERCEL_DEPLOY_HOOK_URL`

Every push to `main` will now automatically build, test, package container images to GHCR, and trigger fresh live deployments on Render and Vercel!
