import { useState, useEffect } from 'react'
import { DialoguePanel } from './DialoguePanel'

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  compliance_monitor: '合规监测',
  anomaly_analysis: '异常分析',
  opportunity_scanner: '商机扫描',
  sales_suggestion: '销售策略',
  sales_coach_analyst: '销售教练',
  knowledge_worker: '知识维护',
}

interface AgentInsight {
  agent_name: string
  insight_text: string
  agent_key: string
  details: Record<string, any>
  confidence: number
}

interface AgentInsightResponse {
  insights: AgentInsight[]
}

interface AgentInsightBarProps {
  pageId: string
}

export default function AgentInsightBar({ pageId }: AgentInsightBarProps) {
  const [loading, setLoading] = useState(true)
  const [insights, setInsights] = useState<AgentInsight[]>([])
  const [dismissed, setDismissed] = useState(false)
  const [error, setError] = useState(false)

  const [activeAgentKey, setActiveAgentKey] = useState<string | undefined>()
  const [activeAgentName, setActiveAgentName] = useState<string>('')
  const [activeContext, setActiveContext] = useState<Record<string, any>>({})
  const [dialogueOpen, setDialogueOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setDismissed(false)
    setError(false)

    fetch(`/api/v1/agent/insights?page=${pageId}`)
      .then((res) => {
        if (!res.ok) throw new Error("fetch failed")
        return res.json()
      })
      .then((data: AgentInsightResponse) => {
        if (!cancelled) {
          const mapped = data.insights.map((insight) => ({
            agent_name: AGENT_DISPLAY_NAMES[insight.agent_key] || insight.agent_key,
            insight_text: insight.summary,
            agent_key: insight.agent_key || '',
            details: insight.details || {},
            confidence: insight.confidence ?? 0,
          }))
          setInsights(mapped)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true)
          setInsights([])
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [pageId])

  const handleAsk = (insight: AgentInsight) => {
    setActiveAgentKey(insight.agent_key)
    setActiveAgentName(AGENT_DISPLAY_NAMES[insight.agent_key] || insight.agent_key)
    setActiveContext({
      summary: insight.insight_text,
      agent_key: insight.agent_key,
      details: insight.details,
      confidence: insight.confidence,
    })
    setDialogueOpen(true)
  }

  if (dismissed) return null
  if (loading)
    return (
      <div className="h-12 animate-pulse rounded-md bg-[var(--clr-gray-20)]" />
    )
  if (error || insights.length === 0) return null

  return (
    <>
      <div className="border-l-4 border-[var(--clr-brand)] bg-[var(--clr-brand-light)] rounded-r-md p-3 flex items-start gap-3 relative">
        <div className="flex-1 space-y-2 pr-4">
          {insights.map((insight, i) => (
            <div key={i} className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-sm text-[var(--clr-brand)]">
                  {insight.agent_name}
                </span>
                <span className="ml-2 text-sm text-[var(--clr-text-primary)]">
                  {insight.insight_text}
                </span>
              </div>
              <button
                className="shrink-0 ml-3 text-xs text-[var(--clr-brand)] hover:text-[var(--clr-brand-dark)] border border-[var(--clr-brand)] rounded px-2 py-0.5 transition-colors"
                onClick={() => handleAsk(insight)}
                aria-label="追问"
              >
                ?
              </button>
            </div>
          ))}
        </div>
        <button
          className="shrink-0 text-[var(--clr-gray-50)] hover:text-[var(--clr-text-primary)] transition-colors"
          onClick={() => setDismissed(true)}
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <DialoguePanel
        isOpen={dialogueOpen}
        onClose={() => setDialogueOpen(false)}
        agentKey={activeAgentKey}
        agentName={activeAgentName}
        context={activeContext}
      />
    </>
  )
}