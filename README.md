# ThunderCast AI

**SIH26084 — Convective-scale nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr)**

Smart India Hackathon 2026 conceptual submission. AI-powered Convective Weather
Intelligence and Decision Support Platform.

---

## Overview

Severe convective weather — thunderstorms, hail, and cloudbursts — can develop
and strike within a matter of hours, causing damage to life, property,
agriculture, and infrastructure. Traditional forecasting excels at large-scale
and medium-range weather, but struggles with the short **0–6 hour nowcasting
window** where convective cells rapidly intensify, move, and dissipate.

ThunderCast AI is a production-deployable AI and geospatial web platform for
**0–6 hour convective nowcasting**. Unlike a generic weather dashboard, it
combines the complete hazard lifecycle:

> **DETECT → PREDICT → TRACK → EXPLAIN → WARN**

The platform provides a Dashboard, probabilistic Forecasts, a Convective Risk
Map, Storm Tracking, Impact-Based Alerts, Historical Event analytics, an AI/ML
Engine status report, impact-based risk scores, and AI Explainability — all
presented in a responsive, mobile-friendly web application.

> **Honest demo note:** at this stage every data module serves clearly-labelled
> **DEMO DATA** produced by a rule-based risk engine. There is no claim of
> trained-model accuracy, real satellite/radar intelligence, or validated
> forecast skill. The architecture is ready for real data ingestion, model
> training, and evaluation in later stages.

## Live Demo

- **Frontend (Vercel):** <https://thundercast-ai.vercel.app>
- **Backend (Render):** <https://thundercast-ai-backend.onrender.com>
- **API documentation (Swagger):** <https://thundercast-ai-backend.onrender.com/docs>
- **Health check:** <https://thundercast-ai-backend.onrender.com/api/health>

## Key Features

| Module | Purpose |
| --- | --- |
| Dashboard | Overview of current convective risk, live conditions & active watches |
| Forecast | Probabilistic 0–6 hr nowcasts per location |
| Risk Map | Geographic visualization of localized hazard risk (Leaflet) |
| Storm Tracking | Movement and evolution of storm cells (historic + projected) |
| Alerts | Impact-based severity-levelled warnings |
| Historical Events | Analysis and analytics of past convective events |
| Methodology | Explainability, model documentation & honest AI status |

Additional capabilities:

- **Impact-Based Risk** — prototype impact scores (flooding, roads, agriculture,
  waterlogging, lightning, hail, visibility).
- **Monthly Activity Analytics** — historical trends, peak months, most-affected
  regions.
- **AI/ML status** — the backend reports an honest `UNTRAINED` /
  `dataset_required` model state rather than fabricated accuracy figures.

## Architecture

```
   Browser
     │
     ▼
 Vercel React frontend (thundercast-ai.vercel.app)
     │  (HTTPS + CORS)
     ▼
 Render FastAPI backend (thundercast-ai-backend.onrender.com)
     │
     ▼
 MongoDB Atlas (MongoDB: optional at this stage)
```

- The **browser never connects directly to MongoDB**.
- All secrets live in environment variables (never in code or Git).
- The backend starts and reports health **even when MongoDB is unavailable**.

### Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Leaflet, Axios, Recharts |
| Backend | Python, FastAPI, Pydantic, PyMongo |
| Database | MongoDB Atlas (optional) |
| Hosting | Vercel (frontend), Render (backend) |

## Repository Structure

```
thundercast-ai/
├── frontend/   # React + TypeScript + Vite + Tailwind + Leaflet
├── backend/    # FastAPI + PyMongo (Python 3.11)
├── docs/       # Documentation
├── render.yaml # Render Blueprint (backend web service)
├── .gitignore
├── README.md
└── LICENSE
```

## Local Setup

Run the frontend and backend together.

### Prerequisites

- **Node.js** 22.x (LTS)
- **Python** 3.11+
- **MongoDB Atlas** is **optional** — the backend runs and serves demo data
  even when no database is configured.

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows (Command Prompt / PowerShell):
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies (add requirements-dev.txt to run tests):
pip install -r requirements.txt

# Optional: copy backend/.env.example to backend/.env and set MONGO_URI if you
# have Atlas. This step is NOT required to run the app with demo data.

# Start the API:
uvicorn app.main:app --reload --port 8000
```

Verify: open <http://localhost:8000/docs> (Swagger) or
<http://localhost:8000/api/health> — it returns `{"status":"healthy", ...}`
even without MongoDB.

### 2. Frontend

```bash
cd frontend
npm install

# Optional: point the API at a local backend for local development
# Copy frontend/.env.example to frontend/.env.local and set
#   VITE_API_BASE_URL=http://localhost:8000
# (Without this file the app defaults to the deployed production backend.)

npm run dev        # http://localhost:5173
```

### 3. Tests & Build

```bash
# Backend tests (from backend/, virtualenv active):
pip install -r requirements-dev.txt
python -m pytest

# Frontend production build (from frontend/, runs tsc type-check first):
npm run build
```

## Environment Variables

Copy the example files and fill in real values. **Never commit real secrets.**

### Frontend — `frontend/.env.example`

```
VITE_API_BASE_URL=http://localhost:8000
```

- `VITE_API_BASE_URL` is read at build time by Vite and baked into the bundle.
- In production (Vercel) this is set to
  `https://thundercast-ai-backend.onrender.com`; the code falls back to the
  deployed backend URL when the variable is unset.
- `VITE_API_URL` is accepted as a backward-compatible alias.

### Backend — `backend/.env.example`

```
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/<db>
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

- `FRONTEND_URL` is the CORS allow-list (comma-separated). In production it is
  set on Render to the deployed frontend origin, e.g.
  `https://thundercast-ai.vercel.app`.
- `MONGO_URI` is optional; the health endpoint reports `"database":
  "unavailable"` when no database is configured, and the app stays functional.

> The backend health endpoint does **not** require MongoDB. The application
> starts successfully and reports health even when the database is unreachable.

## Deployment Strategy

### Frontend → Vercel

- **Root directory:** `frontend`
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Environment variable:** `VITE_API_BASE_URL=https://thundercast-ai-backend.onrender.com`
- SPA routing and asset caching are configured in `frontend/vercel.json`.

### Backend → Render

The repo includes a ready-made `render.yaml` (Blueprint). Live service:

- **URL:** <https://thundercast-ai-backend.onrender.com>
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check path:** `GET /api/health` (returns `200` regardless of
  database state).
- **Environment variables:** `ENVIRONMENT=production`,
  `FRONTEND_URL=<frontend Vercel URL>`, optional `MONGO_URI`.

### Database → MongoDB Atlas

1. Create a free **M0** cluster in Atlas.
2. Add a database user and allow your app's IP / deploy region.
3. Paste the connection URI (`mongodb+srv://...`) into `MONGO_URI` on Render.
   The connection is lazy and resilient — the backend never blocks startup on
   the database.

> The browser never connects to MongoDB directly. All traffic goes through the
> FastAPI backend, and all secrets live in environment variables (never in code
> or Git).

## Roadmap

- **Stage 0 (this repo):** project foundation, health endpoint, app shell,
  responsive navigation, deployment-ready structure, a **rule-based risk
  engine** with explainable risk factors, 0–6 hr demo nowcast, storm cell/track
  demo, alerts, historical analytics, an interactive risk map (free Leaflet +
  CARTO/OpenStreetMap tiles, no API key), and honest `UNTRAINED` ML status — all
  clearly labelled demo data.
- **Stage 1+:** real data ingestion, feature engineering, trained ML models,
  nowcasting, storm tracking, alert generation, historical analysis.

The risk engine is a **domain-inspired heuristic** (not a trained ML model) and
has not been evaluated against real-world data. No weather/satellite/radar APIs,
authentication, or production data ingestion are implemented yet — the foundation
is kept clean and deployable, with all data clearly marked as demo.