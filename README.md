# ThunderCast AI

**SIH26084 — Convective-scale nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr)**

Smart India Hackathon 2026 conceptual submission.

---

## The SIH Problem

Severe convective weather — thunderstorms, hail, and cloudbursts — can develop and
strike within a matter of hours, causing damage to life, property, agriculture, and
infrastructure. Traditional forecasting excels at large-scale and medium-range weather,
but struggles with the short **0–6 hour nowcasting window** where convective cells
rapidly intensify, move, and dissipate. India urgently needs tools that can detect,
track, and warn about these localized, rapidly-evolving hazards in near-real-time.

## ThunderCast AI Concept

ThunderCast AI is a production-deployable AI and geospatial web platform for **0–6 hour
convective nowcasting**. Unlike a generic weather dashboard, it combines the complete
hazard lifecycle:

> **DETECT → PREDICT → TRACK → EXPLAIN → WARN**

The platform is built to:

1. Detect hazardous convective conditions.
2. Predict thunderstorm probability.
3. Predict hail probability.
4. Predict cloudburst / extreme rainfall risk.
5. Generate probabilistic 0–6 hour nowcasts.
6. Visualize risk geographically.
7. Track the movement of hazardous weather cells.
8. Explain *why* a location has elevated risk.
9. Generate impact-based warnings.
10. Provide historical event analysis.
11. Provide model confidence and uncertainty.
12. Support future integration of satellite/radar data.

### Planned Modules

| Module | Purpose |
| --- | --- |
| Dashboard | Overview of current convective risk & active watches |
| Risk Map | Geographic visualization of localized hazard risk |
| Forecast | Probabilistic 0–6 hr nowcasts per location |
| Storm Tracking | Movement and evolution of storm cells |
| Alerts | Impact-based warnings |
| Historical Events | Analysis of past convective events |
| Methodology | Explainability & model documentation |

---

## Architecture

```
   Browser
     │
     ▼
 Vercel React frontend
     │  (HTTPS)
     ▼
 Render FastAPI backend
     │
     ▼
 MongoDB Atlas
```

- The **browser never connects directly to MongoDB**.
- All secrets live in environment variables.
- The backend can start and report health **even when MongoDB is unavailable**.

### Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, PyMongo |
| Database | MongoDB Atlas |
| Hosting | Vercel (frontend), Render (backend) |

---

## Repository Structure

```
thundercast-ai/
├── frontend/   # React + TypeScript + Vite + Tailwind
├── backend/    # FastAPI + PyMongo
├── docs/       # Documentation
├── .gitignore
├── README.md
└── LICENSE
```

---

## Local Setup

Run the frontend and backend together. The frontend calls the backend at
`VITE_API_URL` (default `http://localhost:8000`).

### Prerequisites

- **Node.js** 22.x (LTS) — see `frontend/.nvmrc`
- **Python** 3.11+ — see `backend/runtime.txt`
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

# Optional: create your local env file
# Copy backend/.env.example to backend/.env and set MONGO_URI if you have Atlas.
# This step is NOT required to run the app with demo data.

# Start the API:
uvicorn app.main:app --reload --port 8000
```

Verify the backend: open <http://localhost:8000/docs> (Swagger) or
<http://localhost:8000/api/health> — it returns `{"status":"healthy", ...}`
even without MongoDB.

### 2. Frontend

```bash
cd frontend
npm install

# Optional: point the API at a different backend
# Copy frontend/.env.example to frontend/.env and set VITE_API_URL
# e.g. VITE_API_URL=http://localhost:8000
# (The default fallback used by the code is http://localhost:8000.)

npm run dev        # http://localhost:5173
```

Open <http://localhost:5173> in a browser. The header shows the API as
**Operational** when the backend is reachable and a **DEMO MODE** badge on
every page because all data is clearly-labelled demo data.

### 3. Tests & Build

```bash
# Backend tests (from backend/, virtualenv active):
pip install -r requirements-dev.txt
python -m pytest

# Frontend production build (from frontend/):
npm run build    # runs tsc type-check + vite build
```

---

## Environment Variables

Copy the example files and fill in real values. **Never commit real secrets.**

### Frontend — `frontend/.env.example`

```
VITE_API_URL=http://localhost:8000
```

### Backend — `backend/.env.example`

```
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/<db>
FRONTEND_URL=http://localhost:5173
```

> The backend health endpoint does **not** require MongoDB. The application starts
> successfully and reports health even when the database is unreachable.

---

## Deployment Strategy

### Frontend → Vercel

The `frontend/` directory is a Vite SPA. Deploy it with:

1. Import the `frontend/` directory into Vercel.
2. Set the **Root Directory** to `frontend`.
3. Set the build command to `npm run build` and the output directory to `dist`
   (Vercel detects Vite automatically).
4. In **Environment Variables**, set `VITE_API_URL` to your deployed Render
   backend URL, e.g. `https://thundercast-backend.onrender.com`.
5. SPA routing and asset cache headers are configured in `frontend/vercel.json`.

> `VITE_API_URL` is baked into the bundle at build time, so it must be set
> before `npm run build` runs. The browser reads it through
> `src/lib/config.ts` (`import.meta.env.VITE_API_URL`).

### Backend → Render

The repo includes a ready-made `render.yaml` (Blueprint) for the FastAPI
backend. To deploy manually:

1. Create a **Web Service** pointing at the repository with **Root Directory**
   set to `backend`.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set **Environment Variables**:
   - `MONGO_URI` — MongoDB Atlas connection string (optional; the API runs
     without a database and reports `"database": "unavailable"`).
   - `FRONTEND_URL` — your deployed frontend URL (CORS origin), e.g.
     `https://thundercast.vercel.app`.
   - `ENVIRONMENT=production`
5. Use `GET /api/health` as the health check path (returns `200` regardless of
   database state).

### Database → MongoDB Atlas

1. Create a free **M0** cluster in Atlas.
2. Add a database user and allow your app's IP / deploy region.
3. Paste the connection URI (`mongodb+srv://...`) into `MONGO_URI` on Render.
   The connection is lazy and resilient — the backend never blocks startup on
   the database.

> The browser never connects to MongoDB directly. All traffic goes through the
> FastAPI backend, and all secrets live in environment variables (never in code
> or Git).

---

## Roadmap

- **Stage 0 (this repo):** project foundation, health endpoint, app shell, responsive
  navigation, deployment-ready structure. Implemented now: a **rule-based risk engine**
  with explainable risk factors, 0–6 hr demo nowcast, storm cell/track demo, alerts,
  historical analytics, and an interactive risk map — all clearly labelled demo data.
- **Stage 1+:** real data ingestion, feature engineering, trained ML models, nowcasting,
  storm tracking, alert generation, historical analysis.

The risk engine is a **domain-inspired heuristic** (not a trained ML model) and has not
been evaluated against real-world data. No weather/satellite/radar APIs, authentication,
or production data ingestion are implemented yet — the foundation is kept clean and
deployable, with all data clearly marked as demo.
