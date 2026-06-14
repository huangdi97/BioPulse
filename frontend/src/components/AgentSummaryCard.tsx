import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"

interface AgentSummaryCardProps {
  title: string
  agentKey: string
  pageId: string
  variant: "summary" | "suggestion" | "pulse"
}

interface AgentSummaryResponse {
  summary: string
  details?: Record<string, string>
}

const variantStyles = {
  summary: {
    borderColor: "border-l-blue-500",
    icon: "📊",
  },
  suggestion: {
    borderColor: "border-l-green-500",
    icon: "💡",
  },
  pulse: {
    borderColor: "border-l-orange-500",
    icon: "❤️",
  },
}

export default function AgentSummaryCard({
  title,
  agentKey,
  pageId,
  variant,
}: AgentSummaryCardProps) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<AgentSummaryResponse | null>(null)
  const [error, setError] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    setDismissed(false)

    fetch(`/api/v1/agent/insights?page=${pageId}`)
      .then((res) => res.json())
      .then((body: AgentSummaryResponse) => {
        if (!cancelled) {
          setData(body)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [pageId])

  if (dismissed) return null

  const styles = variantStyles[variant]

  if (loading) {
    return (
      <Card className="p-4 mb-3">
        <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4 mb-2" />
        <div className="h-3 bg-gray-200 rounded animate-pulse w-full" />
      </Card>
    )
  }

  if (error || !data) return null

  const detailEntries = data.details
    ? Object.entries(data.details).slice(0, 3)
    : []

  return (
    <Card
      className={`p-4 mb-3 border-l-4 ${styles.borderColor} relative`}
    >
      <button
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-sm leading-none"
        onClick={() => setDismissed(true)}
      >
        ✕
      </button>
      <div className="pr-4">
        <h4 className="text-sm font-semibold text-gray-800 mb-1">
          {styles.icon} {title}
        </h4>
        <p className="text-sm text-gray-600 mb-2">{data.summary}</p>
        {detailEntries.length > 0 && (
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {detailEntries.map(([key, value]) => (
              <span key={key} className="text-xs text-gray-500">
                <span className="font-medium">{key}:</span> {value}
              </span>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}