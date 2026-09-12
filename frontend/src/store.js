import { configureStore, createSlice } from '@reduxjs/toolkit'

const emptyDraft = {
  source: 'Email', customer_name: '', product_name: '', product_strength: '', batch_number: '', affected_quantity: '',
  manufacturing_date: '', expiry_date: '', complaint_category: '', complaint_description: '', sample_available: 'Unknown', market: ''
}
const emptyAssessment = {
  risk_level: 'Pending', risk_score: 0, rationale: '', completeness_score: 0, missing_information: [], regulatory_flag: false,
  regulatory_note: '', duplicate_signal: 'Run analysis to check the QMS history', recommended_actions: [], root_cause_hypotheses: [], sla: 'Pending triage'
}

const fallbackAnalysis = (text, source = 'Email') => {
  const isOos = /assay|potency|oos|out.of.spec|result/i.test(text)
  const form = isOos ? {
    source, customer_name: 'Northstar Generics', product_name: 'Metformin Hydrochloride Tablets', product_strength: '500 mg',
    batch_number: 'MET-2605-04', affected_quantity: '1 batch', manufacturing_date: '06 May 2026', expiry_date: 'Apr 2029',
    complaint_category: 'Quality / Assay', complaint_description: 'Distributor reports an out-of-specification assay result of 94.1% against the 95.0–105.0% specification for one sampled batch. Product is on hold pending laboratory review.', sample_available: 'Yes — sample in laboratory', market: 'United Kingdom'
  } : {
    source, customer_name: 'Apollo Pharmacy', product_name: 'Amoxicillin 500 mg Capsules', product_strength: '500 mg', batch_number: 'AMX-2403-17',
    affected_quantity: '12 packs', manufacturing_date: '18 Mar 2026', expiry_date: 'Feb 2029', complaint_category: 'Packaging / Container Closure',
    complaint_description: 'Customer reports that twelve packs were received with loose bottle caps and powder residue on the outer carton. No patient injury reported. Investigation and replacement requested.', sample_available: 'Yes — retained sample requested', market: 'India'
  }
  const assessment = {
    risk_level: isOos ? 'Major' : 'Minor', risk_score: isOos ? 72 : 42, completeness_score: 92,
    rationale: isOos ? 'Potential product quality impact requires QA triage and a documented investigation. Product is reported on hold.' : 'Packaging defect reported with no patient injury stated. Verify scope, retain sample and assess recurrence.',
    missing_information: [], regulatory_flag: isOos,
    regulatory_note: isOos ? 'Assess reportability and pharmacovigilance obligations before closure.' : 'No immediate regulatory trigger detected from intake; confirm during triage.',
    duplicate_signal: isOos ? 'No similar OOS complaint in the current QMS history' : 'Possible related complaint: CC-2026-0041 (54%)', duplicate_score: isOos ? 0 : 54,
    duplicate_matches: isOos ? [] : [{ complaint_id: 'CC-2026-0041', product: 'Amoxicillin 500 mg Capsules', batch: 'AMX-2402-08', similarity_score: 54, reason: 'Overlapping product, category and complaint language' }],
    recommended_actions: ['Place affected stock on QA hold pending triage', 'Request photographs and retain / market sample', 'Review batch packaging and distribution records', 'Open CAPA if a systemic or recurring cause is confirmed'],
    root_cause_hypotheses: isOos ? ['Laboratory method or sample preparation variability', 'Manufacturing process drift or blend uniformity issue', 'Distribution / storage excursion requiring temperature review'] : ['Container-closure torque or line clearance control', 'Handling damage during secondary packaging or transit', 'Label / batch record mismatch requiring reconciliation'],
    capa_trigger: isOos, capa_recommendation: isOos ? 'Open a quality-system CAPA after investigation confirms a systemic or recurring cause.' : 'Open a packaging-focused CAPA if the defect is confirmed or recurs.',
    capa_actions: ['Document root cause and define corrective / preventive actions', 'Assign an owner and verify effectiveness before complaint closure'], capa_owner: 'QA / Manufacturing / QC', capa_due_window: isOos ? 'Open within 5 business days' : 'Reassess during complaint closure',
    sla: isOos ? 'QA triage within 24 hours' : 'QA triage within 5 business days'
  }
  return { form_data: form, assessment, summary: form.complaint_description, mode: 'demo-fallback', source_filename: null, agent_trace: [
    {agent: 'Intake Extractor', detail: 'Demo parser mapped narrative to complaint form fields', status: 'complete'},
    {agent: 'Completeness Checker', detail: '92% complete · 0 follow-up items', status: 'complete'},
    {agent: 'Risk Assessor', detail: `Draft classification: ${assessment.risk_level} · ${assessment.risk_score}/100`, status: 'complete'},
    {agent: 'Investigation Planner', detail: 'Prepared 4 recommended next step(s)', status: 'complete'}
  ]}
}

const initialState = {
  draft: emptyDraft,
  assessment: emptyAssessment,
  summary: '',
  trace: [],
  documentMetadata: {},
  assistantMessages: [{ id: 'welcome', role: 'assistant', text: 'Ready to help with complaint intake. You can paste an email, describe what happened, or upload a source document.' }],
  isAnalyzing: false,
  isSaving: false,
  savedId: null,
  error: null,
  complaints: [],
  metrics: { total: 0, open: 0, critical: 0, avg_days: 0, ai_assisted: 0 },
  activeNav: 'Complaints',
  source: 'Email'
}

const slice = createSlice({
  name: 'complaints',
  initialState,
  reducers: {
    setDraftField: (state, action) => { state.draft[action.payload.key] = action.payload.value; state.savedId = null },
    setSource: (state, action) => { state.source = action.payload; state.draft.source = action.payload },
    setActiveNav: (state, action) => { state.activeNav = action.payload },
    setIsAnalyzing: (state, action) => { state.isAnalyzing = action.payload },
    setIsSaving: (state, action) => { state.isSaving = action.payload },
    setError: (state, action) => { state.error = action.payload },
    addMessage: (state, action) => { state.assistantMessages.push({ id: `${Date.now()}-${Math.random()}`, ...action.payload }) },
    setAnalysis: (state, action) => {
      const a = action.payload
      state.draft = { ...state.draft, ...a.form_data }
      state.assessment = a.assessment || emptyAssessment
      state.summary = a.summary || ''
      state.trace = a.agent_trace || []
      state.documentMetadata = a.document_metadata || {}
      state.error = null
      state.assistantMessages.push({ id: `${Date.now()}-result`, role: 'assistant', text: 'I have drafted the complaint record and completed an initial AI risk assessment. Please review the highlighted fields before saving to the QMS ledger.', result: true })
    },
    setComplaints: (state, action) => { state.complaints = action.payload },
    setMetrics: (state, action) => { state.metrics = { ...state.metrics, ...action.payload } },
    setSaved: (state, action) => { state.savedId = action.payload; state.isSaving = false },
    resetDraft: (state) => { Object.assign(state, { draft: { ...emptyDraft }, assessment: { ...emptyAssessment }, summary: '', trace: [], documentMetadata: {}, savedId: null, error: null, assistantMessages: [{ id: `welcome-${Date.now()}`, role: 'assistant', text: 'Ready for a new complaint. Paste an email, describe what happened, or upload a source document.' }] }) }
  }
})

export const { setDraftField, setSource, setActiveNav, setIsAnalyzing, setIsSaving, setError, addMessage, setAnalysis, setComplaints, setMetrics, setSaved, resetDraft } = slice.actions
export const store = configureStore({ reducer: { complaints: slice.reducer } })
export { fallbackAnalysis }
