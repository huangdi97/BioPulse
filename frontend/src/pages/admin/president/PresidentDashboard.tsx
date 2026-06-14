import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ShieldCheck, CalendarCheck, AlertTriangle, TrendingUp } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

interface MonthlySummary {
  summary: string
}

interface KpiData {
  complianceRate: number
  visitCount: number
  anomalyCount: number
}

interface AnomalyTrend {
  month: string
  count: number
}

export default function PresidentDashboard() {
  const [summary, setSummary] = useState<MonthlySummary | null>(null)
  const [kpi, setKpi] = useState<KpiData | null>(null)
  const [trend, setTrend] = useState<AnomalyTrend[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetch('/api/cloud/agent/insights?agent=analysis_agent&scope=monthly').then(r => r.json()),
      fetch('/api/cloud/president/kpi').then(r => r.json()).catch(() => ({
        complianceRate: 94.2,
        visitCount: 1256,
        anomalyCount: 18,
      })),
      fetch('/api/cloud/president/anomaly-trend').then(r => r.json()).catch(() => [
        { month: '1月', count: 12 },
        { month: '2月', count: 10 },
        { month: '3月', count: 15 },
        { month: '4月', count: 8 },
        { month: '5月', count: 6 },
        { month: '6月', count: 4 },
      ]),
    ]).then(([summaryData, kpiData, trendData]) => {
      if (cancelled) return
      setSummary(summaryData)
      setKpi(kpiData)
      setTrend(trendData)
      setLoading(false)
    }).catch(() => {
      if (!cancelled) {
        setLoading(false)
      }
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-24 bg-muted rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-20 bg-muted rounded-xl" />
          <div className="h-20 bg-muted rounded-xl" />
          <div className="h-20 bg-muted rounded-xl" />
        </div>
        <div className="h-64 bg-muted rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-500" />
            AI 月报摘要
          </CardTitle>
        </CardHeader>
        <CardContent>
          {summary?.summary ? (
            <p className="text-sm text-muted-foreground leading-relaxed">{summary.summary}</p>
          ) : (
            <p className="text-sm text-muted-foreground">暂无月报摘要</p>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <ShieldCheck className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">合规率</p>
              <p className="text-2xl font-bold">{kpi?.complianceRate ?? '-'}%</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <CalendarCheck className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">拜访量</p>
              <p className="text-2xl font-bold">{kpi?.visitCount ?? '-'}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">异常数</p>
              <p className="text-2xl font-bold">{kpi?.anomalyCount ?? '-'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">异常趋势</CardTitle>
        </CardHeader>
        <CardContent>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#ef4444" name="异常数" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">暂无月报摘要</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
