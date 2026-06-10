import { useEffect, useState } from 'react'

interface TraceItem {
  trace_id: string
  agent_name: string
  status: string
  total_duration_ms: number
  started_at: string
}

interface TraceDetail {
  trace_id: string
  agent_name: string
  status: string
  total_duration_ms: number
  total_prompt_tokens: number
  total_completion_tokens: number
  tool_calls_json: string
  llm_calls_json: string
  input_data: string
  output_data: string
  started_at: string
  ended_at: string
}

const AGENT_NAMES = [
  'compliance_monitor',
  'sales_suggestion',
  'anomaly_analysis',
  'sales_coach_analyst',
  'opportunity_scanner',
  'knowledge_worker',
  'competitor_crawler',
]

export default function AgentTraceDashboard() {
  const [traces, setTraces] = useState<TraceItem[]>([])
  const [selectedTrace, setSelectedTrace] = useState<TraceDetail | null>(null)
  const [filterAgent, setFilterAgent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pageSize = 20

  const fetchTraces = async (agentName = filterAgent) => {
    setLoading(true)
    setError(null)
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
      const params = new URLSearchParams({ page: '1', page_size: String(pageSize) })
      if (agentName) params.set('agent_name', agentName)
      const res = await fetch(`${baseUrl}/agent/traces?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setTraces(json.data?.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch traces')
    } finally {
      setLoading(false)
    }
  }

  const fetchTraceDetail = async (traceId: string) => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
      const res = await fetch(`${baseUrl}/agent/traces/${traceId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setSelectedTrace(json.data || null)
    } catch (err) {
      console.error('Failed to fetch trace detail:', err)
    }
  }

  useEffect(() => {
    fetchTraces()
  }, [])

  const parseTimeline = (trace: TraceDetail) => {
    const events: { type: string; time: string; detail: string }[] = []
    events.push({ type: 'start', time: trace.started_at, detail: 'Agent started' })

    try {
      const toolCalls = JSON.parse(trace.tool_calls_json || '[]')
      toolCalls.forEach((tc: { tool_name: string; timestamp: string }) => {
        events.push({ type: 'tool_call', time: tc.timestamp, detail: `Tool: ${tc.tool_name}` })
      })
    } catch { /* ignore */ }

    try {
      const llmCalls = JSON.parse(trace.llm_calls_json || '[]')
      llmCalls.forEach((lc: { model: string; timestamp: string }) => {
        events.push({ type: 'llm_call', time: lc.timestamp, detail: `LLM: ${lc.model}` })
      })
    } catch { /* ignore */ }

    events.push({ type: 'end', time: trace.ended_at, detail: `Status: ${trace.status}` })
    events.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    return events
  }

  const renderWaterfall = (events: { type: string; time: string; detail: string }[]) => {
    if (events.length < 2) return null
    const start = new Date(events[0].time).getTime()
    const end = new Date(events[events.length - 1].time).getTime()
    const total = end - start || 1

    return (
      <div style={{ marginTop: 16 }}>
        <h4>Execution Timeline</h4>
        {events.map((evt, i) => {
          const t = new Date(evt.time).getTime()
          const offset = ((t - start) / total) * 100
          const width = Math.max(2, ((t - start) / total) * 100)
          const colors: Record<string, string> = {
            start: '#4CAF50',
            tool_call: '#2196F3',
            llm_call: '#FF9800',
            end: '#9E9E9E',
          }
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: 4, fontSize: 13 }}>
              <span style={{ width: 80, color: '#666' }}>{evt.type}</span>
              <div style={{ flex: 1, height: 20, background: '#f0f0f0', borderRadius: 4, position: 'relative', overflow: 'hidden' }}>
                <div
                  style={{
                    position: 'absolute',
                    left: `${offset}%`,
                    width: `${Math.max(width - offset, 2)}%`,
                    height: '100%',
                    background: colors[evt.type] || '#999',
                    borderRadius: 2,
                    minWidth: 4,
                  }}
                />
              </div>
              <span style={{ width: 200, marginLeft: 8, color: '#333' }}>{evt.detail}</span>
            </div>
          )
        })}
      </div>
    )
  }

  const statusColor = (s: string) => {
    const colors: Record<string, string> = { success: '#4CAF50', error: '#f44336', blocked: '#FF9800', timeout: '#9E9E9E' }
    return colors[s] || '#999'
  }

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Agent Trace Dashboard</h1>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
        <select
          value={filterAgent}
          onChange={(e) => {
            setFilterAgent(e.target.value)
            fetchTraces(e.target.value)
          }}
          style={{ padding: '6px 12px', borderRadius: 4, border: '1px solid #ccc' }}
        >
          <option value="">All Agents</option>
          {AGENT_NAMES.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
        <button onClick={() => fetchTraces()} style={{ padding: '6px 16px', borderRadius: 4, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}>
          Refresh
        </button>
      </div>

      {error && <div style={{ color: '#f44336', marginBottom: 12 }}>{error}</div>}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ flex: selectedTrace ? 1 : 'none', width: selectedTrace ? 'auto' : '100%' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f5f5f5' }}>
                  <th style={{ padding: 8, textAlign: 'left', borderBottom: '2px solid #ddd' }}>Trace ID</th>
                  <th style={{ padding: 8, textAlign: 'left', borderBottom: '2px solid #ddd' }}>Agent</th>
                  <th style={{ padding: 8, textAlign: 'left', borderBottom: '2px solid #ddd' }}>Status</th>
                  <th style={{ padding: 8, textAlign: 'right', borderBottom: '2px solid #ddd' }}>Duration (ms)</th>
                  <th style={{ padding: 8, textAlign: 'left', borderBottom: '2px solid #ddd' }}>Started</th>
                </tr>
              </thead>
              <tbody>
                {traces.length === 0 ? (
                  <tr><td colSpan={5} style={{ padding: 16, textAlign: 'center', color: '#999' }}>No traces found</td></tr>
                ) : (
                  traces.map((t) => (
                    <tr
                      key={t.trace_id}
                      onClick={() => fetchTraceDetail(t.trace_id)}
                      style={{ cursor: 'pointer', background: selectedTrace?.trace_id === t.trace_id ? '#e3f2fd' : 'transparent' }}
                    >
                      <td style={{ padding: 8, borderBottom: '1px solid #eee', fontFamily: 'monospace', fontSize: 12 }}>{t.trace_id.slice(0, 8)}...</td>
                      <td style={{ padding: 8, borderBottom: '1px solid #eee' }}>{t.agent_name}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid #eee' }}>
                        <span style={{ color: statusColor(t.status), fontWeight: 600 }}>{t.status}</span>
                      </td>
                      <td style={{ padding: 8, borderBottom: '1px solid #eee', textAlign: 'right' }}>{t.total_duration_ms}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid #eee', fontSize: 12 }}>{new Date(t.started_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {selectedTrace && (
            <div style={{ width: 400, padding: 16, background: '#fafafa', borderRadius: 8, border: '1px solid #eee', fontSize: 13 }}>
              <h3 style={{ margin: '0 0 12px' }}>Trace Detail</h3>
              <div><strong>ID:</strong> <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{selectedTrace.trace_id}</span></div>
              <div><strong>Agent:</strong> {selectedTrace.agent_name}</div>
              <div><strong>Status:</strong> <span style={{ color: statusColor(selectedTrace.status) }}>{selectedTrace.status}</span></div>
              <div><strong>Duration:</strong> {selectedTrace.total_duration_ms}ms</div>
              <div><strong>Tokens:</strong> {selectedTrace.total_prompt_tokens + selectedTrace.total_completion_tokens} (prompt: {selectedTrace.total_prompt_tokens}, completion: {selectedTrace.total_completion_tokens})</div>
              <div><strong>Started:</strong> {new Date(selectedTrace.started_at).toLocaleString()}</div>
              <div><strong>Ended:</strong> {new Date(selectedTrace.ended_at).toLocaleString()}</div>
              {renderWaterfall(parseTimeline(selectedTrace))}
              <button
                onClick={() => setSelectedTrace(null)}
                style={{ marginTop: 12, padding: '4px 12px', borderRadius: 4, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
