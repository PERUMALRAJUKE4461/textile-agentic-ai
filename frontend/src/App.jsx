import { useEffect, useMemo, useRef, useState } from 'react'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Gauge,
  History,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  ShieldCheck,
  Thermometer,
  Waves,
  Wrench,
  XCircle,
  Zap,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const LOOM_IDS = (import.meta.env.VITE_LOOM_IDS || 'L001,L002,L003,L004')
  .split(',')
  .map((id) => id.trim())
  .filter(Boolean)

const initialMessage = {
  role: 'assistant',
  content: 'I can investigate a loom, trace recurring faults, or prioritize the next technician check.',
}

async function apiRequest(path, options = {}) {
  const headers = options.body
    ? { 'Content-Type': 'application/json', ...options.headers }
    : options.headers
  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    ...options,
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `Request failed (${response.status})`)
  }
  return payload
}

function statusMeta(status = '') {
  const value = status.toLowerCase()
  if (value === 'critical') return { label: 'Critical', tone: 'critical', icon: XCircle }
  if (value === 'warning') return { label: 'Warning', tone: 'warning', icon: AlertTriangle }
  return { label: 'Healthy', tone: 'healthy', icon: CheckCircle2 }
}

function formatTimestamp(value) {
  if (!value) return 'Awaiting signal'
  return value.replace(' ', ' · ')
}

function formatLocalDate(value) {
  return value.toLocaleDateString('en-CA')
}

function formatLocalTime(value) {
  return value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function App() {
  const [machines, setMachines] = useState([])
  const [selectedId, setSelectedId] = useState(LOOM_IDS[0])
  const [loadingMachines, setLoadingMachines] = useState(true)
  const [machineError, setMachineError] = useState('')
  const [details, setDetails] = useState({ maintenance: null, diagnosis: null, rootCause: null, advanced: null })
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsError, setDetailsError] = useState('')
  const [activeTab, setActiveTab] = useState('snapshot')
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [messages, setMessages] = useState([initialMessage])
  const [question, setQuestion] = useState('')
  const [assistantLoading, setAssistantLoading] = useState(false)
  const [currentTime, setCurrentTime] = useState(() => new Date())

  async function loadMachines() {
    setLoadingMachines(true)
    setMachineError('')
    const results = await Promise.allSettled(
      LOOM_IDS.map((loomId) => apiRequest(`/api/machines/${loomId}`)),
    )
    const successful = results
      .filter((result) => result.status === 'fulfilled')
      .map((result) => result.value)
    setMachines(successful)
    if (!successful.length) setMachineError('The monitoring service is unavailable. Start the FastAPI backend and try again.')
    else if (successful.length < LOOM_IDS.length) setMachineError('Some looms could not be reached. Showing the available signals.')
    setLoadingMachines(false)
  }

  useEffect(() => {
    loadMachines()
    const interval = window.setInterval(loadMachines, 30000)
    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    const clock = window.setInterval(() => setCurrentTime(new Date()), 1000)
    return () => window.clearInterval(clock)
  }, [])

  const selectedMachine = machines.find((machine) => machine.loom_id === selectedId) || machines[0]

  useEffect(() => {
    if (!selectedMachine) return undefined
    let active = true
    setSelectedId(selectedMachine.loom_id)
    setDetailsLoading(true)
    setDetailsError('')
    Promise.allSettled([
      apiRequest(`/api/machines/${selectedMachine.loom_id}/maintenance`),
      apiRequest(`/api/machines/${selectedMachine.loom_id}/diagnosis`),
      apiRequest(`/api/machines/${selectedMachine.loom_id}/advanced-analysis`),
    ]).then((results) => {
      if (!active) return
      const [maintenance, diagnosis, advanced] = results
      const advancedValue = advanced.status === 'fulfilled' ? advanced.value : null
      setDetails({
        maintenance: maintenance.status === 'fulfilled' ? maintenance.value : null,
        diagnosis: diagnosis.status === 'fulfilled' ? diagnosis.value : null,
        rootCause: advancedValue?.root_cause_analysis || null,
        advanced: advancedValue,
      })
      if (results.some((result) => result.status === 'rejected')) {
        setDetailsError('Some diagnostic detail is unavailable for this loom.')
      }
      setDetailsLoading(false)
    })
    return () => { active = false }
  }, [selectedMachine?.loom_id])

  const summary = useMemo(() => {
    const healthy = machines.filter((machine) => machine.machine_status === 'NORMAL').length
    const warning = machines.filter((machine) => machine.machine_status === 'WARNING').length
    const critical = machines.filter((machine) => machine.machine_status === 'CRITICAL').length
    return { total: LOOM_IDS.length, healthy, warning, critical, problematic: warning + critical }
  }, [machines])

  const mostUrgentMachine = useMemo(
    () => machines.find((machine) => machine.machine_status === 'CRITICAL')
      || machines.find((machine) => machine.machine_status === 'WARNING'),
    [machines],
  )

  function openMostUrgentMachine() {
    if (!mostUrgentMachine) return
    setSelectedId(mostUrgentMachine.loom_id)
    setActiveTab('diagnosis')
    window.requestAnimationFrame(() => {
      document.querySelector('.detail-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  const alerts = useMemo(() => machines.flatMap((machine) => {
    const items = []
    const add = (code, label, tone, detail) => items.push({ code, label, tone, detail, loomId: machine.loom_id })
    if (machine.fault_type === 'LOW_PRODUCTION' || machine.production_rate < 80) add('LOW_PRODUCTION', 'Low production', 'warning', `${machine.production_rate}% output`)
    if (machine.fault_type === 'BEARING_FAULT' || machine.vibration > 3) add('HIGH_VIBRATION', 'High vibration', 'critical', `${machine.vibration} mm/s`)
    if (machine.fault_type === 'OVERHEATING' || machine.temperature > 65) add('HIGH_TEMPERATURE', 'High temperature', 'warning', `${machine.temperature}°C`)
    if (machine.defect_rate > 2) add('HIGH_DEFECT_RATE', 'High defect rate', 'critical', `${machine.defect_rate}% defects`)
    return items
  }), [machines])

  async function submitQuestion(event) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || assistantLoading) return
    setMessages((current) => [...current, { role: 'user', content: trimmed }])
    setQuestion('')
    setAssistantLoading(true)
    try {
      const result = await apiRequest('/api/agent', {
        method: 'POST',
        body: JSON.stringify({
          question: trimmed,
          conversation_history: messages
            .filter((message) => message.role === 'user' || message.role === 'assistant')
            .map(({ role, content }) => ({ role, content })),
        }),
      })
      setMessages((current) => [...current, { role: 'assistant', content: result.response }])
    } catch (error) {
      setMessages((current) => [...current, { role: 'error', content: `Unable to complete the investigation.\n${error.message}` }])
    } finally {
      setAssistantLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Waves size={21} strokeWidth={2.3} /></div>
          <div>
            <p className="eyebrow">TEXTILE / OPERATIONS</p>
            <h1>Production control</h1>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="live-pill"><span className="live-dot" /> Live telemetry</div>
          <button className="icon-button" title="Refresh telemetry" onClick={loadMachines} disabled={loadingMachines}>
            <RefreshCw size={17} className={loadingMachines ? 'spin' : ''} />
          </button>
          <button className="assistant-button" onClick={() => setAssistantOpen(true)}>
            <Bot size={17} /> Ask the agent
          </button>
        </div>
      </header>

      <main className="dashboard">
        <section className="page-intro">
          <div>
            <p className="section-kicker">Shift overview <span>·</span> {formatLocalDate(currentTime)}</p>
            <h2>Make every pick count.</h2>
            <p className="intro-copy">A live view of loom health, output, and the signals most likely to slow the line.</p>
          </div>
          <div className="shift-note"><CalendarClock size={16} /><span>Live time</span><strong>{formatLocalDate(currentTime)} · {formatLocalTime(currentTime)}</strong></div>
        </section>

        {machineError && <div className="system-banner"><CircleAlert size={18} /><span>{machineError}</span><button onClick={loadMachines}>Retry</button></div>}

        <section className="summary-grid" aria-label="Production summary">
          <SummaryCard icon={Gauge} label="Total looms" value={summary.total} note="Configured fleet" tone="neutral" />
          <SummaryCard icon={ShieldCheck} label="Healthy" value={summary.healthy} note="Within thresholds" tone="healthy" />
          <SummaryCard icon={AlertTriangle} label="Warning" value={summary.warning} note="Needs attention" tone="warning" />
          <SummaryCard icon={CircleAlert} label="Problematic" value={summary.problematic} note={summary.critical ? `${summary.critical} critical` : 'No critical looms'} tone={summary.critical ? 'critical' : 'neutral'} />
          <button className={`production-status ${summary.critical ? 'is-critical' : summary.warning ? 'is-warning' : 'is-healthy'}`} onClick={openMostUrgentMachine} disabled={!mostUrgentMachine} title={mostUrgentMachine ? `Open ${mostUrgentMachine.loom_id} diagnosis` : 'No active intervention'}>
            <div className="status-ring"><Activity size={22} /></div>
            <div><span>Overall production</span><strong>{summary.critical ? 'Intervention required' : summary.warning ? 'Running with watchpoints' : 'Running smoothly'}</strong><small>{summary.critical ? `${mostUrgentMachine.loom_id} · ${mostUrgentMachine.fault_type.replaceAll('_', ' ')}` : summary.warning ? `${summary.warning} loom${summary.warning === 1 ? '' : 's'} need attention` : 'All looms within thresholds'}</small></div>
            <ArrowUpRight size={18} />
          </button>
        </section>

        <div className="content-grid">
          <section className="fleet-panel panel">
            <div className="panel-heading">
              <div><p className="section-kicker">Fleet view</p><h3>Loom signals</h3></div>
              <span className="count-label">{machines.length} / {LOOM_IDS.length} connected</span>
            </div>
            <div className="machine-grid">
              {loadingMachines && !machines.length && LOOM_IDS.map((loomId) => <MachineSkeleton key={loomId} />)}
              {!loadingMachines && !machines.length && <EmptyState title="No loom signals" detail="The backend did not return machine telemetry." />}
              {machines.map((machine) => <MachineCard key={machine.loom_id} machine={machine} selected={machine.loom_id === selectedMachine?.loom_id} onSelect={() => { setSelectedId(machine.loom_id); setActiveTab('snapshot') }} />)}
            </div>
          </section>

          <aside className="alerts-panel panel">
            <div className="panel-heading"><div><p className="section-kicker">Live watch</p><h3>Alerts <span className="heading-count">{alerts.length}</span></h3></div><AlertTriangle size={18} className="muted-icon" /></div>
            <div className="alerts-list">
              {!alerts.length && <EmptyState title="Quiet floor" detail="No threshold alerts are active." compact />}
              {alerts.map((alert, index) => <AlertItem key={`${alert.loomId}-${alert.code}-${index}`} alert={alert} onClick={() => { setSelectedId(alert.loomId); setActiveTab('diagnosis') }} />)}
            </div>
          </aside>
        </div>

        {selectedMachine && <section className="detail-panel panel">
          <div className="detail-header">
            <div className="detail-title"><div className="loom-avatar">{selectedMachine.loom_id.slice(-2)}</div><div><p className="section-kicker">Selected machine</p><h3>{selectedMachine.loom_id} <span>{selectedMachine.loom_type}</span></h3><p className="detail-meta"><span className={`status-dot ${statusMeta(selectedMachine.machine_status).tone}`} />{statusMeta(selectedMachine.machine_status).label} <span className="meta-separator">·</span> Updated {formatTimestamp(selectedMachine.timestamp)}</p></div></div>
            <div className="detail-actions"><button className="outline-button" onClick={() => setAssistantOpen(true)}><MessageSquare size={16} /> Ask about {selectedMachine.loom_id}</button></div>
          </div>
          <div className="tabs" role="tablist">
            <button className={activeTab === 'snapshot' ? 'active' : ''} onClick={() => setActiveTab('snapshot')}><Activity size={16} /> Snapshot</button>
            <button className={activeTab === 'diagnosis' ? 'active' : ''} onClick={() => setActiveTab('diagnosis')}><Search size={16} /> Diagnosis</button>
            <button className={activeTab === 'maintenance' ? 'active' : ''} onClick={() => setActiveTab('maintenance')}><History size={16} /> Maintenance</button>
            <button className={activeTab === 'advanced' ? 'active' : ''} onClick={() => setActiveTab('advanced')}><Zap size={16} /> Advanced AI</button>
          </div>
          {detailsError && <div className="detail-warning"><CircleAlert size={16} /> {detailsError}</div>}
          {detailsLoading ? <DetailSkeleton /> : <DetailContent activeTab={activeTab} machine={selectedMachine} details={details} />}
        </section>}
      </main>

      <button className="floating-assistant" onClick={() => setAssistantOpen(true)} title="Open AI assistant"><Bot size={21} /><span>AI assistant</span></button>
      {assistantOpen && <AssistantPanel messages={messages} question={question} setQuestion={setQuestion} loading={assistantLoading} onSubmit={submitQuestion} onClose={() => setAssistantOpen(false)} />}
    </div>
  )
}

function SummaryCard({ icon: Icon, label, value, note, tone }) {
  return <div className={`summary-card ${tone}`}><div className="summary-icon"><Icon size={18} /></div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
}

function MachineCard({ machine, selected, onSelect }) {
  const meta = statusMeta(machine.machine_status)
  const Icon = meta.icon
  return <button className={`machine-card ${selected ? 'selected' : ''}`} onClick={onSelect}>
    <div className="machine-card-top"><div><span className="loom-id">{machine.loom_id}</span><span className="loom-type">{machine.loom_type}</span></div><span className={`status-badge ${meta.tone}`}><Icon size={13} />{meta.label}</span></div>
    <div className="machine-card-primary"><div><span>Production rate</span><strong>{machine.production_rate}<small>%</small></strong></div><div className="efficiency-meter"><span style={{ width: `${Math.min(machine.efficiency, 100)}%` }} /></div><span className="efficiency-label">{machine.efficiency}% efficiency</span></div>
    <div className="metric-row"><Metric icon={Zap} label="RPM" value={machine.rpm} /><Metric icon={Thermometer} label="Temp" value={`${machine.temperature}°`} /><Metric icon={Activity} label="Vibration" value={machine.vibration} /><Metric icon={CircleAlert} label="Defects" value={`${machine.defect_rate}%`} /></div>
    <div className="card-footer"><span>Motor {machine.motor_current} A</span><span>Humidity {machine.humidity}%</span><ChevronRight size={16} /></div>
  </button>
}

function Metric({ icon: Icon, label, value }) { return <div className="metric"><Icon size={14} /><span>{label}</span><strong>{value}</strong></div> }

function AlertItem({ alert, onClick }) {
  return <button className="alert-item" onClick={onClick}><span className={`alert-icon ${alert.tone}`}><AlertTriangle size={15} /></span><span className="alert-copy"><strong>{alert.label}</strong><small>{alert.loomId} <i>·</i> {alert.detail}</small></span><ChevronRight size={16} /></button>
}

function DetailContent({ activeTab, machine, details }) {
  if (activeTab === 'maintenance') return <MaintenanceView history={details.maintenance} />
  if (activeTab === 'advanced') return <AdvancedView analysis={details.advanced} />
  if (activeTab === 'diagnosis') return <DiagnosisView diagnosis={details.diagnosis} rootCause={details.rootCause} />
  return <SnapshotView machine={machine} diagnosis={details.diagnosis} />
}

function SnapshotView({ machine, diagnosis }) {
  const values = [
    ['RPM', machine.rpm, 'rpm'], ['Temperature', `${machine.temperature}°C`, 'thermal'], ['Vibration', `${machine.vibration} mm/s`, 'vibration'], ['Motor current', `${machine.motor_current} A`, 'current'], ['Warp tension', machine.warp_tension, 'tension'], ['Weft tension', machine.weft_tension, 'tension'], ['Humidity', `${machine.humidity}%`, 'environment'], ['Defect rate', `${machine.defect_rate}%`, 'defect'],
  ]
  return <div className="detail-body"><div className="telemetry-grid">{values.map(([label, value, key]) => <div className={`telemetry-cell ${key}`} key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><div className="diagnosis-strip"><div className="strip-icon"><Wrench size={18} /></div><div><span>Latest diagnosis</span><strong>{diagnosis?.diagnosis || 'Diagnosis unavailable'}</strong></div><button onClick={() => document.querySelector('.tabs button:nth-child(2)')?.click()}>Open diagnosis <ArrowUpRight size={15} /></button></div></div>
}

function DiagnosisView({ diagnosis, rootCause }) {
  if (!diagnosis && !rootCause) return <EmptyState title="Diagnosis unavailable" detail="The backend did not return diagnostic evidence for this loom." />
  return <div className="diagnosis-view">
    <div className="diagnosis-summary"><div className="strip-icon"><Search size={18} /></div><div><span>Machine diagnosis</span><strong>{diagnosis?.diagnosis || rootCause?.summary}</strong></div></div>
    <div className="evidence-legend"><span className="fact-label">Observed fact</span><span className="reference-label">Web reference</span><span className="inference-label">Inference</span><span className="recommendation-label">Recommendation</span></div>
    {rootCause?.root_causes?.length ? rootCause.root_causes.map((cause) => <CauseCard key={cause.cause} cause={cause} />) : <EmptyState title="No ranked causes" detail="No supported root causes were returned from the available evidence." compact />}
  </div>
}

function CauseCard({ cause }) {
  const evidence = cause.evidence || {}
  return <article className="cause-card"><div className="cause-heading"><div><span className="cause-number">ROOT CAUSE</span><h4>{cause.cause}</h4></div><div className="confidence"><strong>{cause.confidence_score}%</strong><span>confidence</span></div></div><div className="cause-columns"><EvidenceList title="Observed facts" items={evidence.supporting_machine_observations} type="fact" /><EvidenceList title="Web references" items={evidence.supporting_web_research} type="reference" /><EvidenceList title="Inferences / gaps" items={[evidence.inference, ...(evidence.contradicting_or_missing_evidence || [])]} type="inference" /></div><div className="recommendations"><span className="recommendation-label">Recommended actions</span>{(cause.recommendations || []).map((item) => <div className="recommendation" key={`${item.priority}-${item.action}`}><b>P{item.priority}</b><span>{item.action}</span></div>)}</div></article>
}

function EvidenceList({ title, items = [], type }) {
  return <div className={`evidence-list ${type}`}><span className={`${type}-label`}>{title}</span>{items.length ? items.slice(0, 3).map((item, index) => <div className="evidence-item" key={`${title}-${index}`}><span>{item?.detail || item?.title || item}</span>{item?.url && <a href={item.url} target="_blank" rel="noreferrer" aria-label={`Open ${item.title || 'source'}`}><ArrowUpRight size={12} /></a>}</div>) : <div className="evidence-empty">No evidence returned</div>}</div>
}

function MaintenanceView({ history }) {
  if (!history?.records?.length) return <EmptyState title="No maintenance history" detail="There are no maintenance records available for this loom." />
  return <div className="maintenance-view"><div className="maintenance-summary"><span>Service events</span><strong>{history.record_count}</strong><small>Historical records</small></div><div className="maintenance-table-wrap"><table><thead><tr><th>Date</th><th>Issue</th><th>Action taken</th><th>Technician</th><th>Downtime</th></tr></thead><tbody>{history.records.map((record) => <tr key={`${record.date}-${record.issue}`}><td>{record.date}</td><td><span className="issue-dot" />{record.issue}</td><td>{record.action_taken}</td><td>{record.technician}</td><td>{record.downtime_hours}h</td></tr>)}</tbody></table></div></div>
}

function AdvancedView({ analysis }) {
  if (!analysis) return <EmptyState title="Advanced analysis unavailable" detail="Historical analysis could not be loaded for this loom." />
  const anomalyItems = analysis.anomaly_detection?.anomalies || []
  const riskItems = analysis.failure_risk?.risks || []
  const trendItems = analysis.trend_analysis?.trends || []
  return <div className="advanced-view">
    <div className="advanced-banner"><div className="strip-icon"><Zap size={18} /></div><div><span>Interpretable advanced analysis</span><strong>Predictions are estimates based on {analysis.historical_record_count} telemetry readings.</strong></div></div>
    <div className="advanced-grid">
      <section className="advanced-block"><div className="advanced-block-heading"><div><span className="section-kicker">Signal review</span><h4>Anomalies</h4></div><span className={`severity-pill ${analysis.anomaly_detection?.overall_severity?.toLowerCase() || 'low'}`}>{analysis.anomaly_detection?.overall_severity || 'LOW'}</span></div>{anomalyItems.length ? anomalyItems.slice(0, 5).map((item) => <div className="anomaly-row" key={item.parameter}><div><strong>{item.parameter.replaceAll('_', ' ')}</strong><span>{item.evidence}</span></div><b className={item.severity.toLowerCase()}>{item.anomaly_score}</b></div>) : <div className="advanced-empty">No unusual deviations detected.</div>}</section>
      <section className="advanced-block"><div className="advanced-block-heading"><div><span className="section-kicker">Forward look</span><h4>Maintenance risk</h4></div><strong className={`risk-word ${(analysis.predictive_maintenance?.risk || 'UNKNOWN').toLowerCase()}`}>{analysis.predictive_maintenance?.risk || 'UNKNOWN'}</strong></div><p className="risk-explanation">{analysis.predictive_maintenance?.explanation || analysis.predictive_maintenance?.message}</p>{(analysis.predictive_maintenance?.evidence || []).map((item, index) => <div className="prediction-evidence" key={index}><CheckCircle2 size={13} /><span>{item.detail}</span></div>)}<div className="forecast-row"><div><span>Production forecast</span><strong>{analysis.production_forecast?.forecast == null ? '—' : `${analysis.production_forecast.forecast}%`}</strong></div><div><span>Trend</span><strong>{analysis.production_forecast?.historical_trend || 'Insufficient data'}</strong></div><div><span>Uncertainty</span><strong>{analysis.production_forecast?.uncertainty == null ? '—' : `±${analysis.production_forecast.uncertainty}`}</strong></div></div></section>
    </div>
    <section className="advanced-block trend-block"><div className="advanced-block-heading"><div><span className="section-kicker">Historical movement</span><h4>Trend analysis</h4></div><span className="count-label">{analysis.historical_record_count} readings</span></div>{analysis.trend_analysis?.status === 'insufficient_data' ? <div className="advanced-empty">{analysis.trend_analysis.message}</div> : <div className="trend-list">{trendItems.filter((item) => ['rpm', 'temperature', 'vibration', 'efficiency', 'defect_rate', 'production_rate'].includes(item.parameter)).map((item) => <div className="trend-row" key={item.parameter}><span>{item.parameter.replaceAll('_', ' ')}</span><b className={item.direction}>{item.direction}</b><small>{item.change_percent > 0 ? '+' : ''}{item.change_percent}%</small></div>)}</div>}</section>
    <section className="advanced-block failure-block"><div className="advanced-block-heading"><div><span className="section-kicker">Risk monitor</span><h4>Failure risk estimates</h4></div><span className="count-label">Not a certainty</span></div><div className="risk-grid">{riskItems.map((item) => <div className="risk-card" key={item.failure_mode}><div><strong>{item.failure_mode.replaceAll('_', ' ')}</strong><span>{item.message}</span></div><b className={item.risk.toLowerCase()}>{item.risk}<small>{item.score}</small></b></div>)}</div></section>
    <div className="limitations"><CircleAlert size={15} /><span>{(analysis.limitations || []).join(' ')}</span></div>
  </div>
}

function AssistantMessage({ message }) {
  if (message.role !== 'assistant') {
    return <span>{message.content}</span>
  }
  const html = DOMPurify.sanitize(marked.parse(message.content, { breaks: true, gfm: true }))
  return <div className="assistant-markdown" dangerouslySetInnerHTML={{ __html: html }} />
}

function parseReport(content) {
  const lines = content.split(/\r?\n/)
  const title = lines.find((line) => /^#\s+/.test(line))?.replace(/^#\s+/, '').trim() || 'Loom investigation'
  const sections = []
  let current = null
  lines.forEach((line) => {
    const heading = line.match(/^##\s+(.+)/)
    if (heading) {
      current = { title: heading[1].replace(/^\d+\.\s*/, '').trim(), lines: [] }
      sections.push(current)
    } else if (current && !/^---+$/.test(line.trim())) {
      current.lines.push(line)
    }
  })
  return { title, sections }
}

function renderInline(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '$1').replace(/`(.+?)`/g, '$1').replace(/^[-•]\s*/, '')
}

function ReportSection({ section }) {
  const lines = section.lines.filter((line) => line.trim())
  const tableLines = lines.filter((line) => line.trim().startsWith('|'))
  const contentLines = lines.filter((line) => !line.trim().startsWith('|'))
  const bullets = contentLines.filter((line) => /^\s*[-*•]\s+/.test(line))
  const numbered = contentLines.filter((line) => /^\s*\d+[.)]\s+/.test(line))
  const paragraphs = contentLines.filter((line) => !/^\s*[-*•]\s+/.test(line) && !/^\s*\d+[.)]\s+/.test(line))
  return <section className="assistant-report-section"><div className="assistant-report-section-heading"><span className="report-step">{section.title.match(/^\d+/)?.[0] || '•'}</span><h4>{section.title}</h4></div>{tableLines.length > 1 && <ReportTable lines={tableLines} />}{paragraphs.map((line, index) => <p key={`paragraph-${index}`}>{renderInline(line)}</p>)}{bullets.length > 0 && <ul>{bullets.map((line, index) => <li key={`bullet-${index}`}>{renderInline(line)}</li>)}</ul>}{numbered.length > 0 && <ol>{numbered.map((line, index) => <li key={`number-${index}`}>{renderInline(line).replace(/^\d+[.)]\s+/, '')}</li>)}</ol>}</section>
}

function ReportTable({ lines }) {
  const rows = lines.filter((line) => !/^\s*\|?\s*:?-+/.test(line.replace(/\|/g, ''))).map((line) => line.split('|').slice(1, -1).map((cell) => renderInline(cell.trim()))).filter((row) => row.length > 1)
  if (!rows.length) return null
  return <div className="assistant-report-table-wrap"><table className="assistant-report-table"><thead><tr>{rows[0].map((cell) => <th key={cell}>{cell}</th>)}</tr></thead><tbody>{rows.slice(1).map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{cell}</td>)}</tr>)}</tbody></table></div>
}

function StructuredReport({ content }) {
  const { title, sections } = parseReport(content)
  return <div className="structured-report"><div className="report-header"><div className="report-header-mark"><Search size={16} /></div><div><span>INVESTIGATION REPORT</span><strong>{title.replace(/\s*—\s*["“].*?["”]\s*$/, '')}</strong></div></div>{sections.map((section, index) => <ReportSection section={section} key={`${section.title}-${index}`} />)}</div>
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]))
}

function LegacyAssistantPanel({ messages, question, setQuestion, loading, onSubmit, onClose }) {
  const messagesEndRef = useRef(null)
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  useEffect(() => {
    const textarea = document.querySelector('.assistant-form textarea')
    if (!textarea) return undefined
    textarea.addEventListener('keydown', handleKeyDown)
    return () => textarea.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  return <div className="assistant-overlay" onClick={onClose}><aside className="assistant-panel" onClick={(event) => event.stopPropagation()}><div className="assistant-header"><div className="assistant-title"><div className="assistant-avatar"><Bot size={19} /></div><div><strong>Production assistant</strong><span>Powered by your agent workflow</span></div></div><button className="icon-button" onClick={onClose} title="Close assistant">×</button></div><div className="assistant-messages">{messages.map((message, index) => <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}><span>{message.content}</span></div>)}{loading && <div className="chat-message assistant"><Loader2 size={15} className="spin" /><span>Investigating machine evidence…</span></div>}</div><form className="assistant-form" onSubmit={onSubmit}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a loom or production issue…" rows="2" /><button type="submit" disabled={loading || !question.trim()} title="Send question"><ArrowUpRight size={18} /></button><div className="assistant-hints"><button type="button" onClick={() => setQuestion('Why is L001 producing poorly?')}>Why is L001 producing poorly?</button><button type="button" onClick={() => setQuestion('What should the technician check first?')}>What should be checked first?</button></div></form></aside></div>
}

function AssistantPanel({ messages, question, setQuestion, loading, onSubmit, onClose }) {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <div className="assistant-overlay" onClick={onClose}>
      <aside className="assistant-panel" onClick={(event) => event.stopPropagation()}>
        <div className="assistant-header">
          <div className="assistant-title">
            <div className="assistant-avatar"><Bot size={19} /></div>
            <div><strong>Production assistant</strong><span>Powered by your agent workflow</span></div>
          </div>
          <button className="icon-button" onClick={onClose} title="Close assistant">×</button>
        </div>
        <div className="assistant-messages">
          {messages.map((message, index) => (
            <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
              <AssistantMessage message={message} />
            </div>
          ))}
          {loading && <div className="chat-message assistant"><Loader2 size={15} className="spin" /><span>Investigating machine evidence…</span></div>}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
        <form className="assistant-form" onSubmit={onSubmit}>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={handleKeyDown} placeholder="Ask about a loom or production issue…" rows="2" />
          <button type="submit" disabled={loading || !question.trim()} title="Send question"><ArrowUpRight size={18} /></button>
          <div className="assistant-hints">
            <button type="button" onClick={() => setQuestion('Why is L001 producing poorly?')}>Why is L001 producing poorly?</button>
            <button type="button" onClick={() => setQuestion('What should be checked first?')}>What should be checked first?</button>
          </div>
        </form>
      </aside>
    </div>
  )
}

function MachineSkeleton() { return <div className="machine-card skeleton-card"><div /><div /><div /><div /></div> }
function DetailSkeleton() { return <div className="detail-skeleton"><div /><div /><div /><div /><div /><div /></div> }
function EmptyState({ title, detail, compact = false }) { return <div className={`empty-state ${compact ? 'compact' : ''}`}><CircleAlert size={compact ? 17 : 21} /><strong>{title}</strong><span>{detail}</span></div> }

export default App