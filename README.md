# Heimdall — AI-Powered Residential Security Platform

This project is an MVP (Minimum Viable Product) built during an internship at **AIMLABS**. It was developed as a proof-of-concept, this is a fork of the initial repository and does not contain any extra changes except for the addition of this README.

## What is Heimdall?

Heimdall is a residential/gated-community security management system. It combines:

- A **web app** (React frontend + FastAPI backend) for residents, security guards, and admins to manage visitor passes, alerts, announcements, and the community directory.
- An **AI investigation pipeline** (LangGraph + Gemini) that simulates gate sensor events, detects anomalies (tailgating, forced-open doors, etc.), investigates them with an LLM, and dispatches alerts while adjusting resident "trust scores".
- **Kiosk apps** (Tkinter + OpenCV + face recognition + YOLO) intended to run at physical gate terminals for badge/QR/face-based entry.
- A **RAG chatbot** that answers resident questions using a community handbook indexed in a vector database.

---

## Repository layout

```
heimdall_Intern_project/
├── backend/              FastAPI application — core REST API for the web app
├── frontend/             React (Vite) single-page app — resident/guard/admin UI
├── heimdall_langgraph/   LangGraph-based AI simulation + investigation pipeline (v2)
├── kiosks/                Desktop kiosk apps for physical gate hardware
├── rag_chatbot/          Standalone RAG chatbot service (resident Q&A assistant)
├── heimdall_core/        Standalone resident-seeding utility (Pydantic-validated)
├── build_config/         Model weights used when packaging the kiosk apps
└── (root-level scripts)  Legacy/standalone simulator & helper scripts
```

### `backend/` — Core API server

FastAPI app that backs the web frontend. Talks to MongoDB via `pymongo`.

- `main.py` — app entry point; wires up CORS and all route modules; also exposes `GET /` as a health check.
- `database.py` — MongoDB connection setup plus shared helpers for alerts and profile lookups (save/get/update alerts, assign/dismiss/resolve, fetch resident/guard/admin profiles).
- `schema.py` — all Pydantic request models (auth, provisioning, visitor passes, deliveries, alerts, vehicles).
- `utils.py` — small helpers (random temp-password generator).
- `seed_database.py` — CLI entry point to wipe and re-seed demo data (`python seed_database.py`).
- `services/seed_service.py` — the actual seeding logic (clears collections, generates demo residents/guards/admins).
- `routes/`
  - `auth.py` — resident/guard/admin login and first-time account initialization (temp passcode → password).
  - `admin_provisioning.py` — admin-only endpoints to bulk-generate resident and security guard credentials.
  - `visitor.py` — creates guest, group, worker, and delivery passes with QR codes.
  - `qr.py` — generates a QR code image for a given pass ID.
  - `resident.py` — resident dashboard operations (profile, add/remove vehicles).
  - `delivery.py` — guard-side delivery tracking (pending deliveries, marking arrivals/expiry).
  - `alerts.py` — fetch/assign/dismiss/resolve security alerts per role (admin/guard/resident).
  - `security.py` — logs guard decisions/actions taken on alerts.
  - `announcement.py` — admin broadcasts/announcements shown to residents.
  - `community_directory.py` — combined resident + guard directory listing for admins.
  - `profile.py` — generic profile lookup endpoints by role.

### `frontend/` — Web UI

React 19 + Vite + Tailwind single-page app.

- `src/main.jsx` / `src/App.jsx` — app bootstrap and top-level view routing (login → Resident / Security / Admin dashboards based on session).
- `src/pages/Login.jsx` — unified sign-in/sign-up flow for all three roles.
- `src/pages/ResidentPortal.jsx` — resident dashboard: visitor/guest/worker/group passes, vehicles, alerts, announcements, chatbot.
- `src/pages/GuardDashboard.jsx` — guard dashboard: incoming alerts, pre-approvals, pass verification, feedback on alerts.
- `src/pages/AdminTower.jsx` — admin console: provisioning residents/guards, community directory, broadcasts, alert oversight.
- `src/components/ResidentBot.jsx` — chat widget that talks to the RAG chatbot backend.
- `src/components/GlobalStyles.jsx` — shared keyframe animations/utility classes injected globally.
- `src/services/alerts.js` — fetch wrappers for the alerts API.
- `index.html`, `vite.config.js`, `tailwind.config.js`, `postcss.config.js`, `eslint.config.js` — standard Vite/Tailwind/ESLint tooling config.

### `heimdall_langgraph/` — AI simulation & investigation pipeline (v2)

Self-contained LangGraph pipeline that simulates gate activity and investigates anomalies with an LLM. See [heimdall_langgraph/README.md](heimdall_langgraph/README.md) for full architecture details, setup, and sample output.

- `graph.py` — entry point; wires the polling loop and LangGraph graph together (`python graph.py`).
- `simulator.py` — background daemon thread that generates gate sensor events and runs Tier-1 (rule-based) anomaly detection.
- `nodes.py` — LangGraph nodes: `investigate_node` (calls the LLM) and `dispatch_node` (creates alerts, updates trust scores).
- `state.py` — `SecurityState` TypedDict shared across graph nodes.
- `database.py` — MongoDB + CSV helpers, including trust-score read/write logic.
- `queues.py` — the thread-safe priority queue connecting the simulator thread to the graph loop.
- `cooldown.py` — suppresses duplicate/near-duplicate anomaly signals within a cooldown window.
- `pattern_cache.py` — caches similar-incident lookups to reduce repeated LLM calls.
- `context_generator.py` — enriches a raw anomaly signal with resident/location/weather context before sending it to the LLM.
- `incident_generator.py` — (placeholder/empty, reserved for future incident-generation logic).
- `services/alert_service.py` — builds and routes alert records (severity, target, assignment).
- `scenarios/` — libraries of plausible contextual narratives used to flesh out simulated events:
  - `base.py` — shared `create_scenario()` helper.
  - `tailgating.py`, `door_forced.py`, `cloned_qr.py`, `visitor.py` — scenario/context text banks per anomaly type.
  - `common.py`, `misc.py`, `registry.py` — (placeholders, currently empty/reserved).
- `test.py` — ad-hoc manual test script for `context_generator.enrich_context`.
- `heimdall_persistence.db*` — local SQLite persistence files used by the LangGraph checkpointer (generated at runtime).

### `kiosks/` — Physical gate terminal apps

Desktop (Tkinter/CustomTkinter) applications intended to run on kiosk hardware at entry points, using OpenCV, `face_recognition`, and YOLOv8 for camera-based checks, with MongoDB for badge/QR/face lookups.

- `main_gate.py` — main entry kiosk UI: badge/QR scanning and face verification flow.
- `block_entry.py` — entry-blocking kiosk variant that layers YOLO-based detection on top of face recognition.

Both scripts read the MongoDB connection string from a `MONGO_URI` environment variable (via `python-dotenv`) rather than a hardcoded value — create a `kiosks/.env` file (git-ignored) with `MONGO_URI=mongodb+srv://...` before running them.

### `rag_chatbot/` — Resident Q&A assistant (RAG service)

Standalone FastAPI microservice that answers resident questions using retrieval-augmented generation over the community handbook. Powers the `ResidentBot` widget in the frontend.

- `app.py` — FastAPI app exposing the chat endpoint; retrieves relevant chunks from Chroma and generates an answer via ChatGroq.
- `ingest.py` — one-off script to chunk and embed documents from `data/documents/` into the local Chroma vector store (`python ingest.py`).
- `data/documents/Community_Handbook.pdf` — source document indexed by the chatbot.
- `chroma_db/` — persisted Chroma vector database (generated by `ingest.py`).

### `heimdall_core/`

- `seed_residents.py` — standalone script that seeds/updates the `residents` collection in MongoDB using strict Pydantic schema validation (independent of `backend/services/seed_service.py`).

### `build_config/`

- `yolov8n.pt` — YOLOv8 nano model weights bundled for kiosk packaging/builds.

### Root-level files

- `simulator.py`, `test.py` — earlier/standalone versions of the event simulator and a quick bcrypt hash-generation script, kept alongside the newer `heimdall_langgraph/` pipeline.
- `heimdall_history_simulator.py` — backfills believable historical gate-event data (normal entries + detected anomalies) straight into MongoDB, using the same Tier-1 detector logic as the live pipeline.
- `heimdall_security_residents_actual.csv` — resident roster consumed by the simulators/pipeline.
- `heimdall_persistence.db` — local SQLite persistence file (generated at runtime).
- `yolov8n.pt` — YOLOv8 weights used locally by the kiosk scripts (git-ignored).
- `.vscode/settings.json` — editor settings for this workspace.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| Backend API | FastAPI, Pydantic, MongoDB (pymongo) |
| AI pipeline | LangGraph, LangChain, Google Gemini |
| RAG chatbot | LangChain, Chroma, HuggingFace embeddings, Groq |
| Kiosks | CustomTkinter, OpenCV, face_recognition, Ultralytics YOLOv8 |
| Database | MongoDB Atlas |

## Getting started (high level)

Each module is largely independent and has its own `requirements.txt` (Python) or `package.json` (frontend). At a minimum you'll need a MongoDB connection string and, for the AI pieces, an LLM API key (Gemini for `heimdall_langgraph`, Groq for `rag_chatbot`) set via a `.env` file — see [heimdall_langgraph/README.md](heimdall_langgraph/README.md) for the pipeline's `.env` format.

```bash
# Backend API
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# AI investigation pipeline
cd heimdall_langgraph && pip install -r requirements.txt && python graph.py

# RAG chatbot
cd rag_chatbot && pip install -r requirements.txt && python ingest.py && uvicorn app:app --reload --port 8001

# Kiosk apps (requires a webcam; create kiosks/.env with MONGO_URI first)
cd kiosks && pip install -r requirements.txt && python main_gate.py
```
