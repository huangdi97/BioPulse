import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { AlertTriangle, Activity, ShieldAlert } from "lucide-react"

interface AgentInsightResponse {
  summary: string
  details?: Record<string, string>
}

export default function AgentExecutiveSummary() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<AgentInsightResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)

    fetch("/api/v1/agent/insights?page=manager_dashboard")
      .then((res) => res.json())
      .then((body: AgentInsightResponse) => {
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
  }, [])

  if (loading) {
    return (
      <Card className="p-5">
        <div className="h-5 bg-gray-200 rounded animate-pulse w-1/2 mb-3" />
        <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4 mb-2" />
        <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
      </Card>
    )
  }

  if (error || !data) return null

  const anomalyCount = data.details?.["异常数"] ?? data.details?.["anomalies"] ?? "—"
  const complianceText = data.details?.["合规脉搏"] ?? data.details?.["compliance_pulse"] ?? "—"
  const topRisk = data.details?.["Top 3 风险"] ?? data.details?.["top_risks"] ?? "—"

  return (
    <Card className="p-5 border-l-4 border-l-blue-500">
      <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
        <Activity className="h-4 w-4 text-blue-500" />
        Analysis + Compliance Agent 联合摘要
      </h3>
      <p className="text-sm text-gray-600 mb-3">{data.summary}</p>
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-2 bg-red-50 rounded-lg px-3 py-2">
          <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-gray-500">本周异常</p>
            <p className="text-sm font-bold text-red-600">{anomalyCount}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2">
          <Activity className="h-4 w-4 text-green-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-gray-500">合规脉搏</p>
            <p className="text-sm font-bold text-green-600">{complianceText}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-orange-50 rounded-lg px-3 py-2">
          <ShieldAlert className="h-4 w-4 text-orange-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-gray-500">Top 3 风险</p>
            <p className="text-sm font-bold text-orange-600 truncate">{topRisk}</p>
          </div>
        </div>
      </div>
    </Card>
  )
}