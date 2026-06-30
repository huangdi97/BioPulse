import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-react"

interface CompliancePulseResponse {
  summary: string
  details?: Record<string, string>
}

const METRICS = [
  { key: "红灯", label: "红灯", bg: "bg-red-50", color: "text-red-700" },
  { key: "黄灯", label: "黄灯", bg: "bg-yellow-50", color: "text-yellow-700" },
  { key: "已整改", label: "已整改", bg: "bg-green-50", color: "text-green-700" },
  { key: "待处理", label: "待处理", bg: "bg-orange-50", color: "text-orange-700" },
]

function TrendArrow({ v }: { v?: string }) {
  if (!v || v === "stable") return <Minus className="h-4 w-4 text-gray-400" />
  return v === "up"
    ? <TrendingUp className="h-4 w-4 text-red-500" />
    : <TrendingDown className="h-4 w-4 text-green-500" />
}

export default function AgentCompliancePulse() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<CompliancePulseResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    fetch("/api/v1/agent/insights?page=compliance_overview")
      .then((r) => r.json())
      .then((body: CompliancePulseResponse) => {
        if (!cancelled) { setData(body); setLoading(false) }
      })
      .catch(() => {
        if (!cancelled) { setError(true); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <Card className="p-5">
        <div className="h-5 bg-gray-200 rounded animate-pulse w-1/3 mb-4" />
        <div className="grid grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </Card>
    )
  }

  if (error || !data) return null

  return (
    <Card className="p-5 border-l-4 border-l-violet-500">
      <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
        <Activity className="h-4 w-4 text-violet-500" />
        合规脉搏
      </h3>
      <div className="grid grid-cols-4 gap-3">
        {METRICS.map((m) => {
          const val = data.details?.[m.key] ?? "0"
          const trend = data.details?.[`${m.key}_trend`]
          return (
            <div key={m.key} className={`${m.bg} rounded-lg px-3 py-2.5`}>
              <p className="text-xs text-gray-500 mb-1">{m.label}</p>
              <div className="flex items-center justify-between">
                <span className={`text-lg font-bold ${m.color}`}>{val}</span>
                <TrendArrow v={trend} />
              </div>
            </div>
          )
        })}
      </div>
      {data.summary && (
        <p className="text-xs text-gray-500 mt-3 leading-relaxed">{data.summary}</p>
      )}
    </Card>
  )
}
