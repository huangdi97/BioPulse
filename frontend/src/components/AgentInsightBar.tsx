import { useState, useEffect } from 'react'

interface AgentInsight {
  agent_name: string
  insight_text: string
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

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setDismissed(false)

    fetch(`/api/v1/agent/insights?page=${pageId}`)
      .then((res) => res.json())
      .then((data: AgentInsightResponse) => {
        if (!cancelled) {
          setInsights(data.insights)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setInsights([])
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [pageId])

  if (dismissed) return null
  if (loading)
    return (
      <div className="h-12 animate-pulse rounded-md bg-[var(--clr-gray-20)]" />
    )
  if (insights.length === 0) return null

  return (
    <div className="border-l-4 border-[var(--clr-brand)] bg-[var(--clr-brand-light)] rounded-r-md p-3 flex items-start gap-3 relative">
      <div className="flex-1 space-y-2 pr-4">
        {insights.map((insight, i) => (
          <div key={i}>
            <span className="font-semibold text-sm text-[var(--clr-brand)]">
              {insight.agent_name}
            </span>
            <span className="ml-2 text-sm text-[var(--clr-text-primary)]">
              {insight.insight_text}
            </span>
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
  )
}