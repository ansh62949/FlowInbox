# FlowInbox AI — Production Deployment & Environment Guide

This guide details the exact environment variable keys, cloud database connections, and step-by-step deployment procedure for hosting **FlowInbox AI** on **Render** (FastAPI Backend) and **Vercel** (Vite Frontend).

---

## 1. Backend Deployment on Render (FastAPI Web Service)

### A. Web Service Configuration
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Connect your GitHub repository: `https://github.com/ansh62949/FlowInbox`.
3. Configure the service settings:
   - **Name:** `flowinbox-backend`
   - **Root Directory:** `flowinbox/backend`
   - **Runtime:** `Docker` (uses `Dockerfile` and `docker-entrypoint.sh`)
   - **Dockerfile Path:** `./Dockerfile`
   - **Health Check Path:** `/api/v1/health`

> **Note on Migrations & Dynamic Port Binding:**
> The `docker-entrypoint.sh` script automatically runs database migrations (`alembic upgrade head`) before launching Uvicorn and binds dynamically to Render's allocated `$PORT` environment variable.

### B. Production Environment Variables (Exact Key Names)

Add the following environment variables in the Render Dashboard (**Environment** tab):

| Environment Variable Key | Value / Description | Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Environment mode | `production` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@ep-xyz.neon.tech/flowinbox_db?sslmode=require` |
| `REDIS_URL` | Upstash / Managed Redis connection URL | `rediss://default:pass@redis-xyz.upstash.io:6379` |
| `QDRANT_URL` | Qdrant Cloud cluster URL | `https://xyz-cluster.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant Cloud API key | `your_qdrant_api_key_here` |
| `GROQ_API_KEY` | Groq LLM API Key | `gsk_...` |
| `GROQ_MODEL` | Groq Catalog Model Name | `llama-3.3-70b-versatile` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIza...` |
| `GEMINI_MODEL` | Gemini Catalog Model Name | `gemini-1.5-flash` |
| `JWT_SECRET` | Secure 256-bit random JWT signature secret | Generate with `openssl rand -hex 32` |
| `OAUTH_TOKEN_ENCRYPTION_KEY` | 32-character key for Fernet token encryption | `secret_key_32_bytes_long_for_fernet!!` |
| `GOOGLE_CLIENT_ID` | Google Cloud OAuth Client ID | `13849...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google Cloud OAuth Client Secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | Exact backend OAuth callback URL | `https://flowinbox-backend.onrender.com/api/v1/auth/google/callback` |
| `FRONTEND_URL` | Live Vercel Frontend URL | `https://flowinbox.vercel.app` |
| `FRONTEND_ORIGINS` | Allowed CORS Origins | `https://flowinbox.vercel.app` |
| `ENABLE_GMAIL_SYNC` | Background email sync flag | `true` |

> ⚠️ **Critical OAuth Setup Step:**
> In your [Google Cloud Console](https://console.cloud.google.com/apis/credentials), select your OAuth 2.0 Client ID and add `https://flowinbox-backend.onrender.com/api/v1/auth/google/callback` under **Authorized Redirect URIs**. Without this exact URI, Google OAuth login will fail with `redirect_uri_mismatch`.

---

## 2. Frontend Deployment on Vercel (Vite React SPA)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New...** → **Project**.
2. Import repository `ansh62949/FlowInbox`.
3. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Edit and set to `flowinbox/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Set the following **Environment Variable**:

| Variable Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://flowinbox-backend.onrender.com/api/v1` |

5. Click **Deploy**. Vercel will build and host your production React application. Client-side route rewrites are pre-configured via [`vercel.json`](file:///c:/Users/satam/OneDrive/Desktop/ai-engineering-bootcamp-prerequisites-1/flowinbox/frontend/vercel.json).

---

## 3. GitHub Actions Continuous Deployment Webhooks (Optional)

Whenever you push to the `main` branch, GitHub Actions builds and pushes multi-arch Docker images to GHCR (`ghcr.io/ansh62949/flowinbox-backend`).

To automatically trigger live deployment on Render and Vercel after build verification:
1. Copy the **Deploy Hook URL** from Render Web Service Settings.
2. Copy the **Deploy Hook URL** from Vercel Project Settings.
3. In GitHub Repository (`ansh62949/FlowInbox`) → **Settings** → **Secrets and variables** → **Actions**, add:
   - `RENDER_DEPLOY_HOOK_URL`
   - `VERCEL_DEPLOY_HOOK_URL`
