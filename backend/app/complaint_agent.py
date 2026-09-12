"""LangGraph workflow for complaint intake.

The graph deliberately separates extraction, completeness, risk and action nodes so each
AI decision is inspectable in the UI. With no Groq key, the same graph runs a deterministic
fixture: this keeps the product demo usable while preserving the production integration.
"""
from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from .config import settings
from .schemas import AnalysisResponse, Assessment, ComplaintForm

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover - the requirements install LangGraph
    StateGraph = None
    START = "__start__"
    END = "__end__"


class ComplaintState(TypedDict, total=False):
    raw_text: str
    source: str
    filename: str | None
    document_metadata: dict[str, Any]
    history: list[dict[str, Any]]
    form_data: dict[str, Any]
    assessment: dict[str, Any]
    summary: str
    trace: list[dict[str, str]]
    mode: str


def _trace(state: ComplaintState, agent: str, detail: str, status: str = "complete") -> list[dict[str, str]]:
    return [*state.get("trace", []), {"agent": agent, "detail": detail, "status": status}]


def _fixture_form(raw: str, source: str) -> dict[str, Any]:
    text = raw.lower()
    # The copy is intentionally realistic but clearly a demo record. In production, this
    # node is replaced by the Gemma structured-output call below.
    if "leak" in text or "bottle" in text or "cap" in text:
        return {
            "source": source,
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin 500 mg Capsules",
            "product_strength": "500 mg",
            "batch_number": "AMX-2403-17",
            "affected_quantity": "12 packs",
            "manufacturing_date": "18 Mar 2026",
            "expiry_date": "Feb 2029",
            "complaint_category": "Packaging / Container Closure",
            "complaint_description": "Customer reports that twelve packs were received with loose bottle caps and powder residue on the outer carton. No patient injury reported. Investigation and replacement requested.",
            "sample_available": "Yes — retained sample requested",
            "market": "India",
        }
    if "assay" in text or "potency" in text or "result" in text:
        return {
            "source": source,
            "customer_name": "Northstar Generics",
            "product_name": "Metformin Hydrochloride Tablets",
            "product_strength": "500 mg",
            "batch_number": "MET-2605-04",
            "affected_quantity": "1 batch",
            "manufacturing_date": "06 May 2026",
            "expiry_date": "Apr 2029",
            "complaint_category": "Quality / Assay",
            "complaint_description": "Distributor reports an out-of-specification assay result of 94.1% against the 95.0–105.0% specification for one sampled batch. Product is on hold pending laboratory review.",
            "sample_available": "Yes — sample in laboratory",
            "market": "United Kingdom",
        }
    return {
        "source": source,
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin 500 mg Capsules",
        "product_strength": "500 mg",
        "batch_number": "AMX-2403-17",
        "affected_quantity": "12 packs",
        "manufacturing_date": "18 Mar 2026",
        "expiry_date": "Feb 2029",
        "complaint_category": "Packaging / Container Closure",
        "complaint_description": "Customer reports that twelve packs were received with loose bottle caps and powder residue on the outer carton. No patient injury reported. Investigation and replacement requested.",
        "sample_available": "Yes — retained sample requested",
        "market": "India",
    }


def _tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", str(value or "").lower()))


def _duplicate_review(form: dict[str, Any], raw: str, history: list[dict[str, Any]]) -> tuple[int, str, list[dict[str, Any]]]:
    """Compare the draft against prior QMS records without sending history to the browser."""
    incoming = _tokens(" ".join([raw, form.get("product_name", ""), form.get("batch_number", ""), form.get("complaint_category", "")]))
    incoming_batch = str(form.get("batch_number") or "").strip().lower()
    matches: list[dict[str, Any]] = []
    for record in history:
        candidate = record.get("form_data") or {}
        candidate_text = " ".join([
            str(record.get("summary", "")), str(record.get("product_name", "")),
            str(record.get("batch_number", "")), str(record.get("complaint_category", "")),
            str(candidate.get("complaint_description", "")),
        ])
        candidate_tokens = _tokens(candidate_text)
        union = incoming | candidate_tokens
        jaccard = len(incoming & candidate_tokens) / len(union) if union else 0
        candidate_batch = str(record.get("batch_number") or candidate.get("batch_number") or "").strip().lower()
        same_batch = bool(incoming_batch and candidate_batch and incoming_batch == candidate_batch)
        score = 96 if same_batch else min(89, round(jaccard * 150))
        if same_batch or score >= 35:
            matches.append({
                "complaint_id": record.get("complaint_id", "Unknown"),
                "product": record.get("product_name") or candidate.get("product_name") or "Unknown product",
                "batch": candidate_batch or "Not recorded",
                "similarity_score": score,
                "reason": "Same batch / lot number" if same_batch else "Overlapping product, category and complaint language",
            })
    matches.sort(key=lambda item: item["similarity_score"], reverse=True)
    matches = matches[:3]
    score = matches[0]["similarity_score"] if matches else 0
    if not matches:
        signal = "No similar complaint found in the current QMS history"
    elif score >= 80:
        signal = f"High similarity to {matches[0]['complaint_id']} ({score}%)"
    else:
        signal = f"Possible related complaint: {matches[0]['complaint_id']} ({score}%)"
    return score, signal, matches


def _capa_plan(form: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    risk = assessment.get("risk_level", "Pending")
    duplicate_score = int(assessment.get("duplicate_score", 0) or 0)
    trigger = risk in ("Major", "Critical") or bool(assessment.get("regulatory_flag")) or duplicate_score >= 65
    category = str(form.get("complaint_category", "")).lower()
    if "pack" in category or "container" in category:
        actions = [
            "Review capping torque, line clearance and packaging equipment maintenance records",
            "Inspect retained and market samples for closure integrity",
            "Trend similar packaging complaints by product and batch",
        ]
        recommendation = "Open a packaging-focused CAPA if the defect is confirmed or recurs."
    elif "assay" in category or "quality" in category or risk in ("Major", "Critical"):
        actions = [
            "Initiate documented root-cause analysis with QA and QC",
            "Review batch manufacturing, laboratory and distribution records",
            "Define effectiveness checks and update the relevant SOP or training if needed",
        ]
        recommendation = "Open a quality-system CAPA after investigation confirms a systemic or recurring cause."
    else:
        actions = [
            "Monitor trend data for recurrence across products and batches",
            "Document the investigation outcome and verify corrective action effectiveness",
        ]
        recommendation = "CAPA is not automatically required; QA should reassess if recurrence or broader impact is identified."
    return {
        "capa_trigger": trigger,
        "capa_recommendation": recommendation,
        "capa_actions": actions,
        "capa_owner": "QA / Manufacturing / QC",
        "capa_due_window": "Open within 5 business days" if trigger else "Reassess during complaint closure",
    }


def _fixture_assessment(form: dict[str, Any], raw: str) -> dict[str, Any]:
    text = raw.lower()
    is_quality = bool(re.search(r"\boos\b|out[- ]of[- ]specification|\bassay\b|\bpotency\b|\badverse\b", text)) or ("injury" in text and "no patient injury" not in text and "no injury" not in text)
    category = form.get("complaint_category", "")
    risk = "Critical" if any(word in text for word in ("death", "hospital", "serious adverse", "contamination")) else ("Major" if is_quality else "Minor")
    score = 86 if risk == "Critical" else (72 if risk == "Major" else 42)
    missing = []
    if not form.get("batch_number"):
        missing.append("Batch / lot number")
    if not form.get("customer_name"):
        missing.append("Customer or reporter name")
    if not form.get("sample_available") or form.get("sample_available") == "Unknown":
        missing.append("Sample availability")
    return {
        "risk_level": risk,
        "risk_score": score,
        "rationale": "Potential product quality impact requires QA triage and a documented investigation. No patient harm is stated in the intake." if risk != "Critical" else "Potential patient safety impact is present; escalate to QA and Pharmacovigilance immediately.",
        "completeness_score": max(60, 100 - len(missing) * 12),
        "missing_information": missing,
        "regulatory_flag": risk == "Critical" or is_quality,
        "regulatory_note": "Assess reportability and pharmacovigilance obligations before closure." if (risk == "Critical" or is_quality) else "No immediate regulatory trigger detected from intake; confirm during triage.",
        "duplicate_signal": "Pending history comparison",
        "duplicate_score": 0,
        "duplicate_matches": [],
        "recommended_actions": [
            "Place affected stock on QA hold pending triage",
            "Request photographs and retain / market sample",
            "Review batch packaging and distribution records",
            "Open CAPA if a systemic or recurring cause is confirmed",
        ],
        "root_cause_hypotheses": [
            "Container-closure torque or line clearance control",
            "Handling damage during secondary packaging or transit",
            "Label / batch record mismatch requiring reconciliation",
        ] if "packaging" in category.lower() else [
            "Laboratory method or sample preparation variability",
            "Manufacturing process drift or blend uniformity issue",
            "Distribution / storage excursion requiring temperature review",
        ],
        "capa_trigger": risk in ("Major", "Critical") or is_quality,
        "capa_recommendation": "Open a quality-system CAPA after investigation confirms a systemic or recurring cause." if risk in ("Major", "Critical") else "CAPA is not automatically required; reassess if recurrence is identified.",
        "capa_actions": [
            "Document root cause and define corrective / preventive actions",
            "Assign an owner and verify effectiveness before complaint closure",
        ],
        "capa_owner": "QA / Manufacturing / QC",
        "capa_due_window": "Open within 5 business days" if risk in ("Major", "Critical") else "Reassess during complaint closure",
        "sla": "QA triage within 24 hours" if risk in ("Critical", "Major") else "QA triage within 5 business days",
    }


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0) if match else text)


def _llm_extract(raw_text: str, source: str) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage

    prompt = f"""You are a pharmaceutical QMS complaint-intake specialist. Extract only what is supported by the complaint and never invent a batch number. Return valid JSON with exactly these keys:
form_data (object with source, customer_name, product_name, product_strength, batch_number, affected_quantity, manufacturing_date, expiry_date, complaint_category, complaint_description, sample_available, market), assessment (object with risk_level one of Minor/Major/Critical, risk_score 0-100, rationale, completeness_score 0-100, missing_information array, regulatory_flag boolean, regulatory_note, duplicate_signal, recommended_actions array, root_cause_hypotheses array, sla), summary (string).
Source channel: {source}
Complaint text: {raw_text}"""
    messages = [
        SystemMessage(content="Return concise, audit-friendly JSON only. Risk assessment is a draft for human QA review, not a final decision."),
        HumanMessage(content=prompt),
    ]
    models = [settings.groq_model]
    if settings.groq_context_model and settings.groq_context_model not in models:
        models.append(settings.groq_context_model)
    last_error: Exception | None = None
    for index, model in enumerate(models):
        try:
            llm = ChatGroq(api_key=settings.groq_api_key, model=model, temperature=0)
            response = llm.invoke(messages)
            parsed = _extract_json(response.content if isinstance(response.content, str) else str(response.content))
            form = ComplaintForm(source=source).model_dump()
            for key, value in (parsed.get("form_data", {}) or {}).items():
                if key in form:
                    form[key] = "" if value is None else str(value)
            raw_assessment = {**(parsed.get("assessment", {}) or {})}
            if isinstance(raw_assessment.get("duplicate_signal"), bool):
                raw_assessment["duplicate_signal"] = "Possible related signal detected" if raw_assessment["duplicate_signal"] else "No similar complaint found"
            for list_key in ("missing_information", "recommended_actions", "root_cause_hypotheses"):
                if raw_assessment.get(list_key) is None:
                    raw_assessment[list_key] = []
            assessment = Assessment(**raw_assessment).model_dump()
            return form, assessment, parsed.get("summary") or form.get("complaint_description", "")[:220], model
        except Exception as exc:
            last_error = exc
            # Groq retired the assignment's requested Gemma model. Try the configured
            # context model so the supplied key still provides a live AI experience.
            message = str(exc).lower()
            can_try_fallback = index == 0 and any(token in message for token in ("decommission", "model_not_found", "does not exist", "not supported"))
            if not can_try_fallback:
                raise
    raise last_error or RuntimeError("No Groq model is configured")


def extract_node(state: ComplaintState) -> ComplaintState:
    if settings.groq_api_key:
        try:
            form, assessment, summary, used_model = _llm_extract(state["raw_text"], state.get("source", "Email"))
            if used_model == settings.groq_model:
                detail = f"{used_model} extracted complaint fields from the submitted text"
                mode = "groq"
            else:
                detail = f"{settings.groq_model} is unavailable; Groq fallback {used_model} extracted complaint fields"
                mode = "groq-fallback"
            return {**state, "form_data": form, "assessment": assessment, "summary": summary, "mode": mode, "trace": _trace(state, "Intake Extractor", detail)}
        except Exception as exc:
            # A failed model call must not discard an intake; switch to a safe demo draft and
            # record the fallback, so the operator can see what happened.
            state = {**state, "trace": _trace(state, "Intake Extractor", f"Groq unavailable; safe fallback used ({type(exc).__name__})", "fallback")}
    form = _fixture_form(state["raw_text"], state.get("source", "Email"))
    return {**state, "form_data": form, "summary": form["complaint_description"], "mode": "demo-fallback", "trace": _trace(state, "Intake Extractor", "Demo parser mapped narrative to complaint form fields")}


def completeness_node(state: ComplaintState) -> ComplaintState:
    assessment = state.get("assessment", {})
    if not assessment:
        assessment = _fixture_assessment(state["form_data"], state["raw_text"])
    else:
        # Keep LLM assessment but normalize one key that the UI depends on.
        assessment = {**_fixture_assessment(state["form_data"], state["raw_text"]), **assessment}
    return {**state, "assessment": assessment, "trace": _trace(state, "Completeness Checker", f"{assessment.get('completeness_score', 0)}% complete · {len(assessment.get('missing_information', []))} follow-up item(s)")}


def duplicate_node(state: ComplaintState) -> ComplaintState:
    assessment = dict(state["assessment"])
    score, signal, matches = _duplicate_review(state["form_data"], state["raw_text"], state.get("history", []))
    assessment.update(duplicate_score=score, duplicate_signal=signal, duplicate_matches=matches)
    detail = f"{signal} · {len(matches)} related record(s) reviewed"
    return {**state, "assessment": assessment, "trace": _trace(state, "Duplicate Detector", detail)}


def risk_node(state: ComplaintState) -> ComplaintState:
    assessment = dict(state["assessment"])
    return {**state, "assessment": assessment, "trace": _trace(state, "Risk Assessor", f"Draft classification: {assessment.get('risk_level')} · {assessment.get('risk_score')}/100")}


def recommendation_node(state: ComplaintState) -> ComplaintState:
    return {**state, "trace": _trace(state, "Investigation Planner", f"Prepared {len(state['assessment'].get('recommended_actions', []))} recommended next step(s)")}


def capa_node(state: ComplaintState) -> ComplaintState:
    assessment = dict(state["assessment"])
    assessment.update(_capa_plan(state["form_data"], assessment))
    status = "CAPA trigger recommended" if assessment.get("capa_trigger") else "CAPA not automatically triggered"
    return {**state, "assessment": assessment, "trace": _trace(state, "CAPA Planner", f"{status} · {assessment.get('capa_due_window')}")}


def build_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(ComplaintState)
    graph.add_node("extract", extract_node)
    graph.add_node("completeness", completeness_node)
    graph.add_node("duplicate", duplicate_node)
    graph.add_node("risk", risk_node)
    graph.add_node("recommendations", recommendation_node)
    graph.add_node("capa", capa_node)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "completeness")
    graph.add_edge("completeness", "duplicate")
    graph.add_edge("duplicate", "risk")
    graph.add_edge("risk", "recommendations")
    graph.add_edge("recommendations", "capa")
    graph.add_edge("capa", END)
    return graph.compile()


GRAPH = build_graph()


def analyze_complaint(raw_text: str, source: str = "Email", filename: str | None = None, history: list[dict[str, Any]] | None = None, document_metadata: dict[str, Any] | None = None) -> AnalysisResponse:
    initial: ComplaintState = {
        "raw_text": raw_text, "source": source, "filename": filename,
        "history": history or [], "document_metadata": document_metadata or {}, "trace": [],
    }
    if GRAPH:
        final = GRAPH.invoke(initial)
    else:
        final = capa_node(recommendation_node(risk_node(duplicate_node(completeness_node(extract_node(initial))))))
    return AnalysisResponse(
        form_data=ComplaintForm(**final["form_data"]),
        assessment=Assessment(**final["assessment"]),
        summary=final.get("summary", ""),
        agent_trace=final.get("trace", []),
        source_filename=filename,
        document_metadata=final.get("document_metadata", {}),
        mode=final.get("mode", "demo-fallback"),
    )
