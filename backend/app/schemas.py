from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ComplaintForm(BaseModel):
    source: str = "Email"
    customer_name: str = ""
    product_name: str = ""
    product_strength: str = ""
    batch_number: str = ""
    affected_quantity: str = ""
    manufacturing_date: str = ""
    expiry_date: str = ""
    complaint_category: str = ""
    complaint_description: str = ""
    sample_available: str = "Unknown"
    market: str = ""


class Assessment(BaseModel):
    risk_level: str = "Pending"
    risk_score: int = Field(default=0, ge=0, le=100)
    rationale: str = ""
    completeness_score: int = Field(default=0, ge=0, le=100)
    missing_information: list[str] = []
    regulatory_flag: bool = False
    regulatory_note: str = ""
    duplicate_signal: str = "No similar complaint found"
    duplicate_score: int = Field(default=0, ge=0, le=100)
    duplicate_matches: list[dict[str, Any]] = []
    recommended_actions: list[str] = []
    root_cause_hypotheses: list[str] = []
    capa_trigger: bool = False
    capa_recommendation: str = ""
    capa_actions: list[str] = []
    capa_owner: str = "QA"
    capa_due_window: str = "Pending triage"
    sla: str = "Pending triage"


class AnalysisResponse(BaseModel):
    form_data: ComplaintForm
    assessment: Assessment
    summary: str
    agent_trace: list[dict[str, str]]
    source_filename: str | None = None
    document_metadata: dict[str, Any] = {}
    mode: str = "demo-fallback"


class ComplaintCreate(BaseModel):
    form_data: ComplaintForm
    assessment: Assessment
    summary: str = ""


class ComplaintOut(BaseModel):
    id: int
    complaint_id: str
    status: str
    risk_level: str
    source: str
    reporter: str
    product_name: str
    batch_number: str
    complaint_category: str
    summary: str
    form_data: dict[str, Any]
    ai_assessment: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
