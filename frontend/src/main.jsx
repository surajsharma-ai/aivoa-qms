import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider, useDispatch, useSelector } from 'react-redux'
import { store, setActiveNav, setAnalysis, setComplaints, setDraftField, setError, setIsAnalyzing, setIsSaving, setMetrics, setSaved, addMessage, fallbackAnalysis, resetDraft, setSource } from './store'
import './styles.css'

const Icon = ({ name, size = 18, stroke = 1.8 }) => {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    inbox: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5V17a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V5.5Z"/><path d="M4 13h4l1.8 2h4.4l1.8-2h4"/></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>,
    shield: <><path d="M12 3 20 6v5c0 5-3.3 8.6-8 10-4.7-1.4-8-5-8-10V6l8-3Z"/><path d="m8.4 12 2.3 2.3 4.9-5"/></>,
    layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>,
    chart: <><path d="M4 19V5M4 19h17"/><path d="m7 15 3-3 3 2 5-7"/></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H12v17H6.5A2.5 2.5 0 0 0 4 22V5.5ZM20 5.5A2.5 2.5 0 0 0 17.5 3H12v17h5.5A2.5 2.5 0 0 1 20 22V5.5Z"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.7 1.7-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-2.4v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L8 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H6.6v-2.4h.2a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L8 8.6l1.7-1.7.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.2h2.4v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.7 1.7-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2V14h-.2a1.7 1.7 0 0 0-1.6 1Z"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    upload: <><path d="M12 16V4M7 9l5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/></>,
    paperclip: <path d="m20.5 11.5-8.8 8.8a5 5 0 0 1-7.1-7.1l9.2-9.2a3.3 3.3 0 0 1 4.7 4.7l-9.3 9.3a1.7 1.7 0 0 1-2.4-2.4l8.4-8.4"/>,
    send: <><path d="m21 3-7.2 18-3.1-7.7L3 10.2 21 3Z"/><path d="m10.7 13.3 4-4"/></>,
    spark: <><path d="m12 2 1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5L12 2Z"/><path d="m19 16 .6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    checkCircle: <><circle cx="12" cy="12" r="9"/><path d="m8 12 2.7 2.7L16 9.5"/></>,
    alert: <><path d="M12 4 21 20H3L12 4Z"/><path d="M12 9v5M12 17h.01"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
    chevron: <path d="m9 18 6-6-6-6"/>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
    microphone: <><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/></>,
    file: <><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></>,
    x: <><path d="m6 6 12 12M18 6 6 18"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    external: <><path d="M14 4h6v6M20 4l-9 9"/><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/></>,
    user: <><circle cx="12" cy="8" r="3.5"/><path d="M5 21a7 7 0 0 1 14 0"/></>,
    refresh: <><path d="M20 11a8 8 0 0 0-14.6-4L3 10M3 5v5h5M4 13a8 8 0 0 0 14.6 4L21 14m0 5v-5h-5"/></>,
    filter: <path d="M4 6h16M7 12h10M10 18h4"/>
  }
  return <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

const nav = [
  { label: 'Overview', icon: 'grid' }, { label: 'Complaints', icon: 'inbox' }, { label: 'Investigations', icon: 'search' },
  { label: 'CAPA', icon: 'shield' }, { label: 'Batch release', icon: 'layers' }, { label: 'Analytics', icon: 'chart' }
]

function App() {
  const dispatch = useDispatch()
  const state = useSelector(s => s.complaints)
  const [showHistory, setShowHistory] = useState(false)
  const [showToast, setShowToast] = useState('')
  const [file, setFile] = useState(null)
  const fileRef = useRef(null)

  useEffect(() => {
    Promise.all([fetch('/api/complaints').then(r => r.ok ? r.json() : Promise.reject()), fetch('/api/dashboard/metrics').then(r => r.ok ? r.json() : Promise.reject())])
      .then(([complaints, metrics]) => { dispatch(setComplaints(complaints)); dispatch(setMetrics(metrics)) }).catch(() => {
        dispatch(setComplaints([
          { complaint_id: 'CC-2026-0041', status: 'Closed', risk_level: 'Minor', source: 'Email', reporter: 'Apollo Pharmacy', product_name: 'Amoxicillin 500 mg Capsules', batch_number: 'AMX-2402-08', complaint_category: 'Packaging / Container Closure', summary: 'Loose cap reported on two packs; no patient impact.' },
          { complaint_id: 'CC-2026-0040', status: 'Under investigation', risk_level: 'Major', source: 'Portal', reporter: 'Northstar Generics', product_name: 'Metformin Hydrochloride Tablets', batch_number: 'MET-2605-04', complaint_category: 'Quality / Assay', summary: 'Distributor reports an assay result below specification.' }
        ])); dispatch(setMetrics({ total: 42, open: 13, critical: 2, avg_days: 4, ai_assisted: 94 }))
      })
  }, [dispatch])

  const updateField = (key, value) => { dispatch(setDraftField({ key, value })); if (key === 'source') dispatch(setSource(value)) }
  const starterText = 'A customer reported that 12 packs of Amoxicillin 500 mg capsules from batch AMX-2403-17 arrived with loose bottle caps and powder residue on the outer cartons. No patient injury reported. Please assess and investigate.'

  const analyze = async (inputText) => {
    const text = (inputText || '').trim()
    if (!text && !file) { dispatch(setError('Add a complaint narrative or choose a source document.')); return }
    dispatch(setError(null)); dispatch(setIsAnalyzing(true)); dispatch(addMessage({ role: 'user', text: file ? `Please analyze ${file.name}` : text }))
    try {
      let response
      if (file) {
        const data = new FormData(); data.append('text', text); data.append('source', state.source); data.append('file', file)
        response = await fetch('/api/complaints/analyze', { method: 'POST', body: data })
      } else {
        response = await fetch('/api/complaints/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, source: state.source }) })
      }
      if (!response.ok) throw new Error('API unavailable')
      dispatch(setAnalysis(await response.json()))
    } catch {
      // The deterministic fixture is useful for the take-home demo and lets the UI be
      // explored without requiring a secret key on the reviewer’s machine.
      dispatch(setAnalysis(fallbackAnalysis(text || 'packaging complaint', state.source)))
    } finally { setFile(null); if (fileRef.current) fileRef.current.value = ''; dispatch(setIsAnalyzing(false)) }
  }

  const saveComplaint = async () => {
    if (!state.draft.product_name || !state.draft.complaint_description) { dispatch(setError('Run AI analysis or complete the product and description fields first.')); return }
    dispatch(setError(null)); dispatch(setIsSaving(true))
    try {
      const res = await fetch('/api/complaints', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ form_data: state.draft, assessment: state.assessment, summary: state.summary }) })
      if (!res.ok) throw new Error('save')
      const record = await res.json(); dispatch(setSaved(record.complaint_id)); dispatch(setComplaints([record, ...state.complaints])); dispatch(setMetrics({ ...state.metrics, total: state.metrics.total + 1, open: state.metrics.open + 1 })); setShowToast(`${record.complaint_id} added to the QMS ledger`)
    } catch {
      const id = `CC-2026-${String(state.metrics.total + 1).padStart(4, '0')}`; dispatch(setSaved(id)); setShowToast(`${id} saved in demo mode`)
    } finally { dispatch(setIsSaving(false)); setTimeout(() => setShowToast(''), 4000) }
  }

  const changeNav = (label) => { dispatch(setActiveNav(label)); if (label !== 'Complaints') setShowToast(`${label} module is available from the QMS navigation`) }

  return <div className="app-shell">
    <Sidebar active={state.activeNav} onSelect={changeNav} />
    <div className="workspace">
      <Topbar onHistory={() => setShowHistory(true)} />
      <main className="page">
        <div className="page-heading">
          <div><div className="eyebrow"><span className="crumb">QMS</span><span>/</span><span>Customer complaints</span></div><h1>Log customer complaint</h1><p className="heading-copy">Capture a complete, audit-ready complaint record with AI-assisted intake.</p></div>
          <div className="heading-actions"><button className="button ghost" onClick={() => dispatch(resetDraft())}><Icon name="refresh" size={15}/> New record</button><button className="button ghost" onClick={() => setShowHistory(true)}><Icon name="clock" size={15}/> Recent complaints</button></div>
        </div>
        <div className="stepper"><div className="step active"><span>1</span><b>Intake</b><small>Draft details</small></div><div className="step-line done"/><div className={`step ${state.assessment.risk_level !== 'Pending' ? 'active' : ''}`}><span>2</span><b>AI assessment</b><small>Risk & completeness</small></div><div className="step-line"/><div className={`step ${state.savedId ? 'active' : ''}`}><span>3</span><b>Review & log</b><small>QMS ledger</small></div><div className="draft-state"><span className={`status-dot ${state.savedId ? 'green' : 'purple'}`}/>{state.savedId ? `Logged as ${state.savedId}` : 'Unsaved draft'}</div></div>
        <div className="content-grid">
          <section className="form-column">
            <ComplaintForm state={state} updateField={updateField} />
            <AssessmentCard assessment={state.assessment} trace={state.trace} />
            {state.error && <div className="error-banner"><Icon name="alert" size={16}/>{state.error}</div>}
            <div className="form-footer"><div className="privacy-note"><Icon name="shield" size={15}/><span>AI output is a draft. QA review and approval are required before final disposition.</span></div><div className="footer-actions"><button className="button text" onClick={() => dispatch(resetDraft())}>Discard</button><button className="button primary" onClick={saveComplaint} disabled={state.isSaving}>{state.isSaving ? <><span className="spinner"/> Saving…</> : <><Icon name="checkCircle" size={16}/> Continue to QMS ledger <Icon name="arrow" size={15}/></>}</button></div></div>
          </section>
          <Copilot state={state} file={file} setFile={setFile} fileRef={fileRef} analyze={analyze} updateField={updateField} useStarter={() => analyze(starterText)} />
        </div>
      </main>
    </div>
    {showHistory && <HistoryModal complaints={state.complaints} close={() => setShowHistory(false)} />}
    {showToast && <div className="toast"><Icon name="checkCircle" size={18}/><span>{showToast}</span><button onClick={() => setShowToast('')}><Icon name="x" size={14}/></button></div>}
  </div>
}

function Sidebar({ active, onSelect }) {
  return <aside className="sidebar"><div className="brand"><div className="brand-mark"><span/><span/><span/></div><div><strong>AIVOA</strong><small>QMS / AI</small></div></div><div className="site-select"><div className="site-avatar">A</div><div><b>Acme Pharma</b><span>Quality Operations</span></div><Icon name="chevron" size={14}/></div><nav>{nav.map(item => <button key={item.label} className={`nav-item ${active === item.label ? 'selected' : ''}`} onClick={() => onSelect(item.label)}><Icon name={item.icon} size={18}/><span>{item.label}</span>{item.label === 'Complaints' && <i className="nav-count">13</i>}</button>)}</nav><div className="sidebar-bottom"><button className="nav-item" onClick={() => onSelect('Settings')}><Icon name="settings" size={18}/><span>Settings</span></button><div className="compliance-chip"><div className="chip-icon"><Icon name="shield" size={16}/></div><div><b>GxP workspace</b><span>21 CFR Part 11 ready</span></div></div><div className="profile"><div className="profile-avatar">KS</div><div><b>Kapish Sharma</b><span>QA Director</span></div><Icon name="chevron" size={14}/></div></div></aside>
}

function Topbar({ onHistory }) {
  return <header className="topbar"><div className="mobile-brand"><div className="brand-mark"><span/><span/><span/></div><b>AIVOA</b></div><div className="topbar-search"><Icon name="search" size={17}/><span>Search complaints, batches or CAPAs</span><kbd>⌘ K</kbd></div><div className="topbar-right"><div className="ai-status"><span className="status-dot green"/>AI services operational</div><button className="icon-button" onClick={onHistory} aria-label="Recent complaints"><Icon name="clock" size={18}/></button><button className="icon-button"><Icon name="book" size={18}/></button><div className="topbar-avatar">KS</div></div></header>
}

const fields = [
  { key: 'source', label: 'Complaint source', options: ['Email', 'Phone', 'Portal', 'Distributor', 'Sales representative'] },
  { key: 'customer_name', label: 'Customer name', placeholder: 'e.g. Apollo Pharmacy' },
  { key: 'product_name', label: 'Product name', placeholder: 'e.g. Amoxicillin 500 mg Capsules' },
  { key: 'product_strength', label: 'Product strength / type', placeholder: 'e.g. 500 mg' },
  { key: 'batch_number', label: 'Batch / lot number', placeholder: 'e.g. AMX-2403-17' },
  { key: 'affected_quantity', label: 'Affected quantity', placeholder: 'e.g. 12 packs' },
  { key: 'manufacturing_date', label: 'Manufacturing date', placeholder: 'e.g. 18 Mar 2026' },
  { key: 'expiry_date', label: 'Expiry date', placeholder: 'e.g. Feb 2029' },
  { key: 'complaint_category', label: 'Complaint category', placeholder: 'e.g. Packaging / Container Closure' }
]

function ComplaintForm({ state, updateField }) {
  return <div className="card form-card"><div className="card-header"><div><h2>Complaint details</h2><p>Review and edit the fields drafted from the source narrative.</p></div><span className="ai-badge"><Icon name="spark" size={13}/> AI assisted</span></div><div className="form-section-label"><span>01</span> Intake information</div><div className="fields-grid">{fields.map(field => <Field key={field.key} field={field} value={state.draft[field.key]} onChange={v => updateField(field.key, v)} />)}</div><div className="form-section-label description-label"><span>02</span> Complaint narrative</div><label className="field full"><span className="field-label">Complaint description <em>Required</em></span><textarea rows="5" value={state.draft.complaint_description} onChange={e => updateField('complaint_description', e.target.value)} placeholder="Describe the issue, what was observed, and any reported patient impact…"/><small>{state.draft.complaint_description.length ? `${state.draft.complaint_description.length} characters` : 'Include what happened, when, and the impact reported by the customer.'}</small></label><div className="mini-fields"><label className="field"><span className="field-label">Sample availability</span><select value={state.draft.sample_available} onChange={e => updateField('sample_available', e.target.value)}><option>Unknown</option><option>Yes — retained sample requested</option><option>Yes — sample in laboratory</option><option>No sample available</option></select></label><label className="field"><span className="field-label">Market / country</span><input value={state.draft.market} onChange={e => updateField('market', e.target.value)} placeholder="e.g. India"/></label></div></div>
}

function Field({ field, value, onChange }) {
  return <label className="field"><span className="field-label">{field.label}{['product_name', 'batch_number'].includes(field.key) && <em>Required</em>}</span>{field.options ? <select value={value || field.options[0]} onChange={e => onChange(e.target.value)}>{field.options.map(option => <option key={option}>{option}</option>)}</select> : <input value={value || ''} onChange={e => onChange(e.target.value)} placeholder={field.placeholder}/>}</label>
}

function AssessmentCard({ assessment, trace }) {
  const ready = assessment.risk_level !== 'Pending'
  return (
    <div className={`card assessment-card ${ready ? 'ready' : ''}`}>
      <div className="card-header">
        <div><h2>AI Copilot risk assessment</h2><p>{ready ? 'Draft assessment generated from the complaint narrative.' : 'Run the copilot to generate a draft risk and completeness assessment.'}</p></div>
        <span className={`risk-pill ${assessment.risk_level.toLowerCase()}`}>{ready ? assessment.risk_level : 'Pending'}</span>
      </div>
      {ready ? (
        <div className="assessment-ready">
          <div className="assessment-summary">
            <div className="score-ring" style={{ '--score': `${assessment.risk_score * 3.6}deg` }}><strong>{assessment.risk_score}</strong><span>/100</span></div>
            <div><b>{assessment.risk_level} priority</b><p>{assessment.rationale}</p><div className="sla"><Icon name="clock" size={13}/>{assessment.sla}</div></div>
          </div>
          <div className="assessment-grid">
            <div className="assessment-item"><span className="item-label">Completeness</span><div className="meter"><span style={{ width: `${assessment.completeness_score}%` }}></span></div><b>{assessment.completeness_score}%</b>{assessment.missing_information?.length > 0 && <small>Missing: {assessment.missing_information.join(', ')}</small>}</div>
            <div className="assessment-item"><span className="item-label">Duplicate signal</span><b className="signal"><span className="signal-dot"></span>{assessment.duplicate_signal}</b><small>{assessment.duplicate_score || 0}% match score · {assessment.duplicate_matches?.length || 0} related record(s) reviewed</small>{assessment.duplicate_matches?.slice(0, 2).map(match => <span className="match-line" key={match.complaint_id}><strong>{match.complaint_id}</strong> · {match.reason}</span>)}</div>
          </div>
          <div className="regulatory-callout"><Icon name={assessment.regulatory_flag ? 'alert' : 'shield'} size={16}/><div><b>{assessment.regulatory_flag ? 'Regulatory review recommended' : 'No immediate regulatory trigger'}</b><span>{assessment.regulatory_note}</span></div></div>
          <div className={`capa-callout ${assessment.capa_trigger ? 'triggered' : ''}`}><div className="capa-icon"><Icon name="shield" size={15}/></div><div><div className="capa-title"><b>CAPA recommendation</b><span className={`capa-tag ${assessment.capa_trigger ? 'open' : 'monitor'}`}>{assessment.capa_trigger ? 'Open after investigation' : 'Monitor'}</span></div><span>{assessment.capa_recommendation}</span><small>{assessment.capa_owner} · {assessment.capa_due_window}</small>{assessment.capa_actions?.length > 0 && <ul>{assessment.capa_actions.slice(0, 2).map(action => <li key={action}>{action}</li>)}</ul>}</div></div>
          {trace.length > 0 && <details className="trace"><summary><span><Icon name="spark" size={13}/> LangGraph agent trace</span><span>{trace.length} nodes <Icon name="chevron" size={13}/></span></summary><div className="trace-list">{trace.map((item, i) => <div key={i}><span className="trace-check"><Icon name="check" size={11}/></span><div><b>{item.agent}</b><span>{item.detail}</span></div></div>)}</div></details>}
        </div>
      ) : (
        <div className="empty-assessment"><div className="empty-icon"><Icon name="spark" size={20}/></div><span>AI assessment will appear here after intake analysis.</span></div>
      )}
    </div>
  )
}

function Copilot({ state, file, setFile, fileRef, analyze, useStarter }) {
  const [text, setText] = useState('')
  const [sourceOpen, setSourceOpen] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const submit = () => { analyze(text); setText('') }
  return <aside className="copilot card"><div className="copilot-head"><div className="copilot-title"><div className="copilot-icon"><Icon name="spark" size={17}/></div><div><h2>AIVOA Copilot</h2><span>Complaint intake assistant</span></div></div><span className="online-dot" title="Online"/></div><div className="copilot-divider"/><div className="copilot-body"><div className="copilot-context"><span className="context-chip"><Icon name="shield" size={12}/> QMS context on</span><span className="context-label">Gemma 2 · human review required</span></div><div className="messages">{state.assistantMessages.map(message => <div key={message.id} className={`message-row ${message.role === 'user' ? 'user-row' : ''}`}><div className={`message-avatar ${message.role === 'user' ? 'user-avatar' : ''}`}>{message.role === 'user' ? 'KS' : <Icon name="spark" size={13}/>}</div><div className={`message ${message.role === 'user' ? 'user-message' : ''} ${message.result ? 'result-message' : ''}`}><p>{message.text}</p>{message.result && <div className="message-result"><span><Icon name="checkCircle" size={13}/> Form fields drafted</span><span><Icon name="checkCircle" size={13}/> Risk assessed</span></div>}</div></div>)}{state.isAnalyzing && <div className="message-row"><div className="message-avatar"><Icon name="spark" size={13}/></div><div className="message thinking"><span className="thinking-dots"><i/><i/><i/></span><span>Reviewing complaint against QMS context…</span></div></div>}</div>{state.documentMetadata?.method && <div className="document-status"><div className="doc-status-icon"><Icon name="file" size={14}/></div><div><b>{state.documentMetadata.method}</b><span>{state.documentMetadata.characters || 0} characters extracted{state.documentMetadata.ocr_used ? ' · OCR applied' : ''}{state.documentMetadata.warning ? ` · ${state.documentMetadata.warning}` : ''}</span></div></div>}{state.assessment.risk_level === 'Pending' && !state.isAnalyzing && <div className="starter"><div className="starter-title"><Icon name="spark" size={13}/> Try a quick example</div><button onClick={useStarter}><span>“Customer received packs with loose caps…”</span><Icon name="arrow" size={14}/></button><button onClick={() => analyze('Distributor reports assay result of 94.1% against a 95.0–105.0% specification for batch MET-2605-04. Product is on hold pending review.')}><span>“Assay result below specification…”</span><Icon name="arrow" size={14}/></button></div>}{file && <div className="file-chip"><Icon name="file" size={15}/><span>{file.name}</span><button onClick={() => setFile(null)}><Icon name="x" size={13}/></button></div>}</div><div className="copilot-input-wrap"><div className={`composer ${isRecording ? 'recording' : ''}`}><textarea value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit() } }} placeholder={isRecording ? 'Listening…' : 'Describe the complaint or paste an email…'} rows="2"/><div className="composer-actions"><div><button className="round-plain" title="Attach complaint document" onClick={() => fileRef.current?.click()}><Icon name="paperclip" size={16}/></button><input type="file" ref={fileRef} className="hidden-file" accept=".pdf,.txt,.eml,.csv,image/*" onChange={e => setFile(e.target.files?.[0] || null)}/><button className={`round-plain ${isRecording ? 'recording-button' : ''}`} title="Voice input" onClick={() => setIsRecording(!isRecording)}><Icon name="microphone" size={16}/></button></div><button className="send-button" onClick={submit} disabled={state.isAnalyzing || (!text.trim() && !file)}><Icon name="send" size={15}/></button></div></div><div className="composer-hint"><span>⌘ Enter to analyze</span><button onClick={() => setSourceOpen(!sourceOpen)}>Source: {state.source} <Icon name="chevron" size={12}/></button></div>{sourceOpen && <div className="source-menu">{['Email', 'Phone', 'Portal', 'Distributor', 'Sales representative'].map(s => <button key={s} onClick={() => { setSourceOpen(false); updateField('source', s) }}>{s}</button>)}</div>}</div><div className="copilot-footer"><Icon name="shield" size={13}/> AI suggestions are logged for auditability <button title="Learn more"><Icon name="external" size={12}/></button></div></aside>
}

function HistoryModal({ complaints, close }) {
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && close()}><div className="modal"><div className="modal-head"><div><span className="eyebrow">QMS / Records</span><h2>Recent complaints</h2><p>Latest records in the complaint ledger.</p></div><button className="icon-button" onClick={close}><Icon name="x" size={18}/></button></div><div className="table-wrap"><table><thead><tr><th>Complaint ID</th><th>Product / customer</th><th>Category</th><th>Risk</th><th>Status</th></tr></thead><tbody>{complaints.slice(0, 8).map(item => <tr key={item.complaint_id}><td><b>{item.complaint_id}</b><small>{item.source}</small></td><td><b>{item.product_name}</b><small>{item.reporter}</small></td><td>{item.complaint_category}</td><td><span className={`table-risk ${item.risk_level.toLowerCase()}`}>{item.risk_level}</span></td><td><span className="status-text"><span className={`status-dot ${item.status === 'Closed' ? 'green' : 'amber'}`}/>{item.status}</span></td></tr>)}</tbody></table></div><div className="modal-foot"><span>{complaints.length} records shown</span><button className="button ghost" onClick={close}>Close</button></div></div></div>
}

createRoot(document.getElementById('root')).render(<Provider store={store}><App /></Provider>)
