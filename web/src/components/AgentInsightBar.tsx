import { useState, useEffect } from "react"

interface Insight {
  agent_name: string
  insight_text: string
}

interface Props {
  pageId: string
}

export default function AgentInsightBar({ pageId }: Props) {
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [visible, setVisible] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    fetch(`/api/v1/agent/insights?page=${pageId}`)
      .then((res) => {
        if (!res.ok) throw new Error("fetch failed")
        return res.json()
      })
      .then((data: Insight[]) => {
        setInsights(data)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [pageId])

  if (loading) {
    return (
      <div className="h-12 animate-pulse rounded-md bg-[var(--clr-gray-20)]" />
    )
  }

  if (error || insights.length === 0 || !visible) return null

  return (
    <div className="border-l-4 border-[var(--clr-brand)] bg-[var(--clr-brand-light)] rounded-r-md p-3 flex items-start gap-3">
      <div className="flex-1 space-y-2">
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
        onClick={() => setVisible(false)}
        className="shrink-0 text-[var(--clr-gray-50)] hover:text-[var(--clr-text-primary)] transition-colors"
        aria-label="Close"
      >
        ✕
      </button>
    </div>
  )
}