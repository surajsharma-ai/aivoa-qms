from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .complaint_agent import analyze_complaint
from .config import settings
from .document_parser import parse_document
from .database import Base, SessionLocal, engine, get_db
from .models import Complaint
from .schemas import AnalysisResponse, ComplaintCreate, ComplaintOut

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(func.count(Complaint.id))) > 0:
        return
    examples = [
        ("CC-2026-0041", "Closed", "Minor", "Email", "Apollo Pharmacy", "Amoxicillin 500 mg Capsules", "AMX-2402-08", "Packaging / Container Closure", "Loose cap reported on two packs; no patient impact.", "08 Apr 2026"),
        ("CC-2026-0040", "Under investigation", "Major", "Portal", "Northstar Generics", "Metformin Hydrochloride Tablets", "MET-2605-04", "Quality / Assay", "Distributor reports an assay result below specification; stock placed on hold.", "06 Apr 2026"),
        ("CC-2026-0039", "Closed", "Minor", "Phone", "MediSource Ltd", "Azithromycin Tablets", "AZI-2603-12", "Appearance", "Tablet chipping reported in one shipper; retain sample passed visual check.", "02 Apr 2026"),
        ("CC-2026-0038", "Draft", "Critical", "Email", "CarePoint Hospital", "Ceftriaxone Injection", "CEF-2601-01", "Potential contamination", "Visible particulate reported in a vial; patient safety escalation opened.", "28 Mar 2026"),
    ]
    for cid, status, risk, source, reporter, product, batch, category, summary, date_label in examples:
        d = {
            "source": source, "customer_name": reporter, "product_name": product, "product_strength": "500 mg", "batch_number": batch,
            "affected_quantity": "See source complaint", "manufacturing_date": "—", "expiry_date": "—", "complaint_category": category,
            "complaint_description": summary, "sample_available": "Unknown", "market": "India"
        }
        db.add(Complaint(complaint_id=cid, status=status, risk_level=risk, source=source, reporter=reporter, product_name=product, batch_number=batch, complaint_category=category, summary=summary, form_data=d, ai_assessment={"risk_level": risk, "risk_score": 86 if risk == "Critical" else 58, "completeness_score": 92, "recommended_actions": []}))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIVOA QMS API</title>
<style>
  :root{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:#252532;background:#f7f8fc}
  *{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px}
  .card{width:min(720px,100%);background:#fff;border:1px solid #e8e8f0;border-radius:18px;padding:36px;box-shadow:0 18px 50px #33306012}
  .brand{display:flex;align-items:center;gap:12px;color:#28213f;font-weight:800;letter-spacing:.08em}.mark{width:34px;height:34px;background:#28213f;border-radius:10px;display:flex;align-items:end;justify-content:center;gap:3px;padding:7px}.mark i{width:4px;border-radius:4px;background:#fff;height:10px}.mark i:nth-child(2){height:18px;background:#a998ff}.mark i:nth-child(3){height:14px}
  h1{font-size:28px;letter-spacing:-.04em;margin:28px 0 8px}p{color:#777988;line-height:1.6;font-size:14px}.ok{display:inline-flex;align-items:center;gap:8px;color:#16865e;background:#eaf8f1;border:1px solid #caefdf;padding:7px 11px;border-radius:999px;font-size:12px;font-weight:700}.dot{width:8px;height:8px;border-radius:50%;background:#2fb884;box-shadow:0 0 0 4px #d9f4e8}.links{display:flex;gap:10px;flex-wrap:wrap;margin-top:25px}.links a{color:#5e45c8;text-decoration:none;background:#f2efff;border:1px solid #e4defe;padding:10px 14px;border-radius:8px;font-size:12px;font-weight:700}.links a:hover{background:#e8e3ff}.endpoints{margin-top:28px;border-top:1px solid #eeeef3;padding-top:18px;color:#676977;font-size:12px;line-height:2}.endpoints code{color:#5343a5;background:#f7f5ff;padding:2px 5px;border-radius:4px;margin-right:8px}
</style></head><body><main class="card"><div class="brand"><span class="mark"><i></i><i></i><i></i></span><span>AIVOA <small>QMS / AI</small></span></div><h1>QMS API is running</h1><span class="ok"><span class="dot"></span>Operational · FastAPI</span><p>The customer complaint service is ready. Use the frontend preview for the full complaint workflow, or open the interactive API documentation to test each endpoint.</p><div class="links"><a href="/docs">Open Swagger docs →</a><a href="/redoc">Open ReDoc →</a><a href="/api/health">Health JSON →</a></div><div class="endpoints"><div><code>GET</code>/api/complaints — complaint ledger</div><div><code>POST</code>/api/complaints/analyze — LangGraph AI intake</div><div><code>POST</code>/api/complaints — save reviewed complaint</div><div><code>GET</code>/api/dashboard/metrics — QMS metrics</div></div></main></body></html>"""


@app.get("/api/health")
def health() -> dict[str, str]:
    configured = bool(settings.groq_api_key)
    return {
        "status": "ok",
        "service": settings.app_name,
        "ai_configured": "true" if configured else "false",
        "ai_model": settings.groq_model if configured else "demo-fallback",
        "ai_fallback_model": settings.groq_context_model if configured else "",
    }


@app.get("/api/dashboard/metrics")
def metrics(db: Session = Depends(get_db)) -> dict[str, int]:
    rows = db.scalars(select(Complaint)).all()
    return {
        "total": len(rows),
        "open": sum(1 for c in rows if c.status != "Closed"),
        "critical": sum(1 for c in rows if c.risk_level == "Critical"),
        "avg_days": 4,
        "ai_assisted": 94,
    }


@app.get("/api/complaints", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)) -> list[Complaint]:
    return list(db.scalars(select(Complaint).order_by(Complaint.created_at.desc())).all())


@app.get("/api/complaints/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)) -> Complaint:
    complaint = db.scalar(select(Complaint).where(Complaint.complaint_id == complaint_id))
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    return complaint


async def parse_intake(request: Request) -> tuple[str, str, str | None, dict[str, object]]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        text = str(form.get("text") or "")
        source = str(form.get("source") or "Email")
        upload = form.get("file")
        filename = None
        metadata: dict[str, object] = {}
        if upload is not None and hasattr(upload, "read"):
            filename = getattr(upload, "filename", None)
            raw = await upload.read()
            extracted_text, metadata = parse_document(raw, filename, getattr(upload, "content_type", None))
            if not text:
                text = extracted_text
            if not text:
                text = "A complaint source document was uploaded, but no readable text was extracted. Review the original evidence and request the missing complaint details."
        return text, source, filename, metadata
    payload = await request.json()
    return str(payload.get("text") or payload.get("prompt") or ""), str(payload.get("source") or "Email"), payload.get("filename"), payload.get("document_metadata") or {}


@app.post("/api/complaints/analyze", response_model=AnalysisResponse)
async def analyze(request: Request, db: Session = Depends(get_db)) -> AnalysisResponse:
    text, source, filename, document_metadata = await parse_intake(request)
    if len(text.strip()) < 8:
        raise HTTPException(422, "Please add a complaint narrative or upload a document.")
    rows = db.scalars(select(Complaint).order_by(Complaint.created_at.desc())).all()
    history = [
        {
            "complaint_id": row.complaint_id,
            "status": row.status,
            "product_name": row.product_name,
            "batch_number": row.batch_number,
            "complaint_category": row.complaint_category,
            "summary": row.summary,
            "form_data": row.form_data or {},
        }
        for row in rows
    ]
    return analyze_complaint(text, source, filename, history=history, document_metadata=document_metadata)


@app.post("/api/complaints", response_model=ComplaintOut)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)) -> Complaint:
    now = datetime.now(timezone.utc)
    next_number = 1 + (db.scalar(select(func.count(Complaint.id))) or 0)
    form = payload.form_data.model_dump()
    assessment = payload.assessment.model_dump()
    complaint = Complaint(
        complaint_id=f"CC-{now.year}-{next_number:04d}", status="Open", risk_level=assessment["risk_level"], source=form["source"],
        reporter=form.get("customer_name") or "Unspecified reporter", product_name=form.get("product_name") or "Unspecified product",
        batch_number=form.get("batch_number") or "Pending", complaint_category=form.get("complaint_category") or "Uncategorized",
        summary=payload.summary or form.get("complaint_description", "")[:280], form_data=form, ai_assessment=assessment,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint
