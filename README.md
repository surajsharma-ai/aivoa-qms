# AIVOA QMS · AI complaint copilot

A demo-ready AI-powered customer complaint management module for pharmaceutical API and FDF manufacturing. The interface follows the provided AIVOA complaint-demo flow: a user pastes an email or uploads a source document, the AI drafts the **Log Customer Complaint** form, runs an initial **AI Copilot Risk Assessment**, and sends the human-reviewed record to the QMS ledger.

## What is implemented

- React + Redux Toolkit frontend with an AIVOA-inspired QMS workspace
- FastAPI backend with typed complaint and assessment APIs
- LangGraph pipeline with inspectable nodes:
  1. Intake Extractor
  2. Completeness Checker
  3. Risk Assessor
  4. Investigation Planner
  5. Duplicate Detector
  6. CAPA Planner
- Groq integration through `langchain-groq` using `gemma2-9b-it` by default, with automatic fallback when Groq retires a model
- Deterministic fallback fixtures when `GROQ_API_KEY` is not configured, so the demo is fully runnable without secrets
- SQLAlchemy persistence compatible with PostgreSQL (Docker Compose) and a local SQLite fallback for quick evaluation
- Complaint source intake from narrative, `.txt`, `.eml`, `.csv`, native PDF text extraction, scanned PDF OCR, and image OCR
- AI-assisted completeness, duplicate signal with related-record matches, risk classification, regulatory review flag, root-cause hypotheses, investigation actions, SLA recommendation, and CAPA recommendation
- Recent complaint history modal, QMS ledger save, GxP human-review guardrail, responsive layout, and audit-friendly LangGraph trace

## Run locally

### 1. Frontend + local API, no secrets required

```bash
# terminal 1
python -m pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# terminal 2
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The backend defaults to `sqlite:///./aivoa_qms.db` so a reviewer can run the demo immediately. The SQLite file is created in `backend/` and is ignored by Git.

### 2. Enable Groq / Gemma

```bash
cp backend/.env.example backend/.env
# set GROQ_API_KEY in backend/.env
# optional: change GROQ_MODEL, but the requested default is gemma2-9b-it
# the app automatically falls back to GROQ_CONTEXT_MODEL when Groq retires a model
```

When a key is present, the same LangGraph graph calls Groq for structured extraction and assessment. If the model call errors, the graph records a fallback trace and returns a safe demo draft instead of losing the complaint.

### 3. PostgreSQL with Docker Compose

```bash
GROQ_API_KEY=your_key docker compose up --build
```

The API container uses PostgreSQL at `db:5432`; the web container is exposed at `http://localhost:5173`.

## End-to-end demo script

1. Open **Complaints → Log customer complaint**.
2. In **AIVOA Copilot**, click the packaging example, or paste an email in plain English.
3. Show the submitted narrative in the chat and the short LangGraph thinking state.
4. Review the form fields drafted on the left: source, customer, product, batch, dates, quantity, category, and description.
5. Expand **LangGraph agent trace** under the assessment to show the four nodes.
6. Edit a form field to demonstrate human review and explain that the AI draft is never treated as final QA disposition.
7. Click **Continue to QMS ledger**. The FastAPI `POST /api/complaints` call creates a complaint ID such as `CC-2026-0005`.
8. Open **Recent complaints** to show the saved record alongside the seeded history.
9. Optional: attach `demo_data/complaint_email.txt` to demonstrate document intake.

## API surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | API and AI mode health |
| GET | `/api/dashboard/metrics` | Complaint counters for the workspace |
| GET | `/api/complaints` | Complaint ledger list |
| POST | `/api/complaints/analyze` | Run LangGraph intake analysis; accepts JSON or multipart upload |
| POST | `/api/complaints` | Persist a human-reviewed complaint record |
| GET | `/api/complaints/{complaint_id}` | Retrieve one complaint |

## Domain assumptions

A pharmaceutical complaint record is more than a customer-service ticket. It is a controlled quality record used to evaluate whether a reported issue may affect product identity, strength, quality, purity, safety, packaging, labeling, or regulatory compliance.

The demo therefore captures the product/batch context, source, customer, quantity, dates, narrative, sample availability, market, risk, completeness, regulatory review, investigation actions, and CAPA signal. The same intake pattern works for:

- **API manufacturing:** batch, process, assay/potency, impurity, contamination, storage/distribution and specification concerns.
- **FDF manufacturing:** dosage form, strength, appearance, packaging/container closure, labeling, patient impact, adverse-event signal and distribution concerns.

Typical QMS sequence: receive → log → acknowledge → validate/completeness check → classify risk → investigate against batch/retention/market evidence → decide reportability and CAPA/recall linkage → communicate → QA approve and close → trend.

This prototype supports the intake and triage slice of that lifecycle. It deliberately keeps the risk score and recommendations as a **draft requiring human QA review**, which is important for a compliant AI-assisted QMS workflow.

## Project layout

```text
frontend/src/main.jsx          UI, intake composer, form, assessment and history
frontend/src/store.js          Redux state and offline demo fixture
frontend/src/styles.css        responsive AIVOA-style visual system
backend/app/complaint_agent.py LangGraph workflow + Groq adapter + safe fallback
backend/app/main.py            FastAPI routes, upload parsing, persistence and seed data
backend/app/document_parser.py PDF text extraction and optional OCR pipeline
backend/app/models.py          SQLAlchemy complaint ledger model
backend/app/schemas.py         typed request/response contracts
demo_data/                     realistic source complaint for upload testing
```
