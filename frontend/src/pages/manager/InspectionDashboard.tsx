import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import AgentInsightBar from '@/components/AgentInsightBar'
import { AlertTriangle, CheckCircle, Clock, ShieldCheck } from 'lucide-react'
import { fetchDashboard } from '@/api/inspection'
import type { InspectionDashboardData } from '@/types/inspection'

export default function InspectionDashboard() {
  const [data, setData] = useState<InspectionDashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchDashboard().then((data) => { if (!cancelled) setData(data) }).finally(() => setLoading(false))
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="p-4 text-sm text-muted-foreground">加载中...</div>
  if (!data) return <div className="p-4 text-sm text-muted-foreground">暂无数据</div>

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_inspection" />
      <div>
        <h2 className="text-lg font-semibold">飞检准备度</h2>
        <p className="text-sm text-muted-foreground">飞行检查准备情况总览与风险评分</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<ShieldCheck className="h-5 w-5 text-blue-600" />} label="自检完成率" value={`${data.self_check_rate}%`} />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} label="逾期项" value={data.overdue_count} />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-green-600" />} label="历史记录" value={data.history_records} />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-red-600" />} label="风险评分" value={data.score} />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-blue-500" />
            风险评分
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="relative w-24 h-24">
              <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
                <circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke={data.score >= 80 ? 'hsl(var(--success))' : data.score >= 60 ? 'hsl(var(--warning))' : 'hsl(var(--destructive))'}
                  strokeWidth="8"
                  strokeDasharray={`${(data.score / 100) * 264} 264`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{data.score}</span>
              </div>
            </div>
            <div className="space-y-1 text-sm">
              <p className="text-muted-foreground">
                评分等级: <span className="font-medium text-foreground">
                  {data.score >= 80 ? '优秀' : data.score >= 60 ? '待改进' : '不合格'}
                </span>
              </p>
              <p className="text-muted-foreground">
                自检完成率: <span className="font-medium text-foreground">{data.self_check_rate}%</span>
              </p>
              <p className="text-muted-foreground">
                逾期项: <span className="font-medium text-foreground">{data.overdue_count} 项</span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
