import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import {
  AlertTriangle,
  ClipboardList,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { fetchComplianceDashboard } from '@/api/compliance'
import type { ComplianceDashboard } from '@/types'

const RISK_BG: Record<string, string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const RISK_LABEL: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }
  componentDidCatch() {
    this.setState({ hasError: true })
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-48 gap-3">
          <p className="text-sm text-muted-foreground">组件渲染异常</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-3 py-1.5 text-sm rounded bg-primary text-primary-foreground"
          >
            重试
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function ComplianceOverview() {
  const [data, setData] = useState<ComplianceDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchComplianceDashboard()
      .then((res) => {
        if (cancelled) return
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Dashboard fetch failed:', err)
        if (cancelled) return
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        加载中...
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="space-y-4">
      <div className="flex gap-4">
        <StatCard
          icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
          label="今日违规"
          value={data.todayViolations}
        />
        <StatCard
          icon={<ClipboardList className="h-5 w-5 text-blue-600" />}
          label="本周总计"
          value={data.weeklyTotal}
        />
        <StatCard
          icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
          label="处理率"
          value={data.processedRate}
        />
        <StatCard
          icon={<ShieldAlert className="h-5 w-5 text-red-600" />}
          label="高风险"
          value={data.highRiskCount}
        />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">近 7 天违规趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.dailyTrend} margin={{ top: 4, left: -20, right: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4, fill: '#3b82f6' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">高频违规类型 TOP3</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.topCategories.map((cat, index) => (
                <div key={cat.category} className="flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-bold shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium flex-1">{cat.category}</span>
                  <div className="w-32 bg-muted rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${cat.percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground w-10 text-right">
                    {cat.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">高频违规代表 TOP3</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {data.topReps.map((rep, index) => (
                <div
                  key={rep.repName}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 ${
                      index === 0
                        ? 'bg-yellow-100 text-yellow-700'
                        : index === 1
                          ? 'bg-gray-100 text-gray-600'
                          : 'bg-orange-100 text-orange-700'
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium flex-1">{rep.repName}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${RISK_BG[rep.riskLevel]}`}
                  >
                    {RISK_LABEL[rep.riskLevel]}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {rep.violationCount} 次
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    </ErrorBoundary>
  )
}
