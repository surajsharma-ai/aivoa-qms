# QMS research notes used for the prototype

These are implementation notes, not regulatory advice. The prototype only demonstrates complaint intake and triage; it is not a validated GxP system.

## Why customer complaints matter

A complaint is a quality signal received from a customer, healthcare provider, distributor, field representative, or other external source. The QMS must preserve the original report, identify the affected product and batch, assess potential patient/product risk, investigate with appropriate evidence, decide whether escalation/reporting/CAPA is needed, communicate an outcome, and retain the record for trending and inspection readiness.

The module therefore treats a complaint as a controlled quality record rather than a support ticket. The form captures source, reporter, product, strength/form, batch/lot, dates, quantity, category, narrative, sample availability and market. The AI output is separated as a draft assessment, and the operator must review before logging.

## API and FDF context

- **API** complaints often need process and laboratory context: assay/potency, impurities, contamination, storage, handling, specification and batch evidence.
- **FDF** complaints often need dosage-form and patient-facing context: strength, appearance, dissolution/assay, packaging/container closure, labeling, adverse-event signals and distribution conditions.
- In either case, the batch/lot number is a key join to manufacturing, testing, distribution and retention-sample records. Missing information should create a follow-up task, not silently become an invented value.

## Workflow represented in the app

`Receive → Log → Completeness check → Risk triage → Investigation plan → Regulatory / CAPA signal → QA review → Ledger`

The current demo stops at the reviewed intake record. A production implementation would link the complaint to controlled batch records, investigation evidence, CAPA, recall, pharmacovigilance and an immutable audit trail.

## Source material

- FDA, **21 CFR § 211.198 Complaint files**: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-J/section-211.198
- FDA, **21 CFR § 211.192 Production record review**: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-J/section-211.192
- FDA, **21 CFR Part 11 Electronic records; electronic signatures**: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11
- ICH, **Q7 Good Manufacturing Practice Guide for Active Pharmaceutical Ingredients**, section 15 (complaints and recalls): https://database.ich.org/sites/default/files/Q7_Guideline.pdf
- AIVOA public product context, including QMS, ICH Q7, 21 CFR Part 11 and human-validation positioning: https://aivoa.ai/

## Safety and compliance design choices

1. **Human in the loop:** risk score, regulatory flag, duplicate signal, root-cause hypotheses and recommended actions are explicitly labeled as draft AI assistance.
2. **Traceability:** the LangGraph node trace is returned to the UI and every AI suggestion can be explained by the complaint narrative and workflow node.
3. **No silent fabrication:** the Groq prompt tells the model to extract only supported facts and never invent the batch number. The demo fallback is deterministic and visibly runs in `demo-fallback` mode.
4. **Audit-ready separation:** AI-generated data is stored under `ai_assessment` and is not treated as a QA-approved disposition.
5. **SLA by risk:** the demo recommends quicker QA triage for Major/Critical drafts, while the final timeline must be configured to the company SOP and applicable regulations.
