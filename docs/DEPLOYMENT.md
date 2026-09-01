# ThunderCast AI Backend — Render Deployment

This document describes how to deploy the FastAPI backend to [Render](https://render.com).

## Runtime

- **Python:** `3.11` (pinned in `backend/runtime.txt` for Render's buildpacks).
- **ASGI server:** Uvicorn.

## Requirements

- `backend/requirements.txt` is pinned to known-compatible versions, including:
  - `fastapi`
  - `uvicorn[standard]`
  - `pydantic` / `pydantic-settings`
  - `pymongo`
  - `python-dotenv`

## Setting up the Web Service on Render

1. Create a new **Web Service** and point it at the repository.
2. Set the **Root Directory** to `backend` (the directory containing
   `requirements.txt`, `runtime.txt` and `app/`).
3. Set the **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
4. Set the **Start Command** (binds `0.0.0.0` and the `PORT` supplied by Render):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   > The port is never hardcoded; Render injects it via the `PORT` environment
   > variable.

5. Add the required **environment variables**:

   | Variable | Example | Purpose |
   | --- | --- | --- |
   | `MONGO_URI` | `mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority` | MongoDB Atlas connection string |
   | `FRONTEND_URL` | `https://thundercast.vercel.app` | Allowed CORS origin(s), comma-separated |
   | `ENVIRONMENT` | `production` | Runtime mode |
   | `MONGO_DB_NAME` | `thundercast` | (optional) database name override |

   Secrets (e.g. the MongoDB password) live only in Render's environment — never
   in code or in Git.

## Startup behaviour with MongoDB

The application **starts successfully even when MongoDB Atlas is unreachable**.

- On startup it does **not** force a connection; it lazily creates a shared
  PyMongo client on first use.
- A short `serverSelectionTimeoutMS` keeps the backend responsive when the
  database is down.
- `GET /api/health` reports `"database": "connected"` only after a successful
  live ping, otherwise `"database": "unavailable"` — the API stays up.

## CORS

CORS origins are read from `FRONTEND_URL` (see `backend/app/config.py`). In
`production` only the configured origins are allowed — a bare `*` is never used.

## Health check

Render can use `GET /api/health` as a health check path. It returns `200` as
long as the process is running, regardless of database state.

## Local run

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
uvicorn app.main:app --reload
```

Swagger docs are available at `http://localhost:8000/docs`.
