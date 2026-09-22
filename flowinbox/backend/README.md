# FlowInbox AI — Backend Service

The backend component for **FlowInbox AI**, built with Python FastAPI, Async SQLAlchemy 2.0, Alembic, LangGraph, and Pydantic v2.

---

## ⚡ Quick Start

### 1. Environment Setup
Create a `.env` file in `flowinbox/backend` based on `.env.production.example`:
```env
DATABASE_URL=postgresql+asyncpg://flowinbox_user:flowinbox_password@localhost:5432/flowinbox_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 2. Install Dependencies
```bash
py -3 -m pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
py -3 -m alembic upgrade head
```

### 4. Start Development Server
```bash
py -3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Running Tests

Run the full pytest suite:
```bash
py -3 -m pytest tests/
```

---

## 🔌 API Documentation
When running locally, Swagger interactive docs are available at:
`http://localhost:8000/docs`
