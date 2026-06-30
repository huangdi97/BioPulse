import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Lightbulb, X } from "lucide-react"

interface AgentDailyBriefResponse {
  summary: string
  details?: Record<string, string>
}

export default function AgentDailyBrief() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<AgentDailyBriefResponse | null>(null)
  const [error, setError] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)

    fetch("/api/v1/agent/insights?page=rep_dashboard")
      .then((res) => res.json())
      .then((body: AgentDailyBriefResponse) => {
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

    return () => { cancelled = true }
  }, [])

  if (dismissed) return null

  if (loading) {
    return (
      <Card className="p-4 border-l-4 border-l-amber-500">
        <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4 mb-2" />
        <div className="h-3 bg-gray-200 rounded animate-pulse w-full" />
      </Card>
    )
  }

  if (error || !data) return null

  return (
    <Card className="p-4 border-l-4 border-l-amber-500 relative">
      <button
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        onClick={() => setDismissed(true)}
      >
        <X className="h-4 w-4" />
      </button>
      <div className="flex items-start gap-3 pr-6">
        <div className="mt-0.5 shrink-0">
          <Lightbulb className="h-5 w-5 text-amber-500" />
        </div>
        <div className="min-w-0">
          <h4 className="text-sm font-semibold text-gray-800 mb-1">
            Suggestion Agent
          </h4>
          <p className="text-sm text-gray-600">{data.summary}</p>
        </div>
      </div>
    </Card>
  )
}