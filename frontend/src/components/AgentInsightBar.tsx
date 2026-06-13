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
      <div className="h-10 bg-gray-200 rounded animate-pulse" />
    )
  if (insights.length === 0) return null

  return (
    <div className="border border-blue-400 rounded p-3 bg-blue-50 relative">
      <button
        className="absolute top-1 right-1 text-gray-400 hover:text-gray-600 text-sm leading-none"
        onClick={() => setDismissed(true)}
      >
        ✕
      </button>
      <div className="space-y-1 pr-4">
        {insights.map((insight, i) => (
          <p key={i} className="text-sm text-gray-700">
            <span className="font-semibold">{insight.agent_name}</span>:{' '}
            {insight.insight_text}
          </p>
        ))}
      </div>
    </div>
  )
}