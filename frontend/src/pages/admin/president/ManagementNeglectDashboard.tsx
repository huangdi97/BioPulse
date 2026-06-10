import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { fetchManagementNeglect } from '@/api/adminPresident'

export default function ManagementNeglectDashboard() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchManagementNeglect>> | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchManagementNeglect().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  const { summary, details } = data

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">未处理红灯</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.unresolvedReds}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">平均响应天数</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.avgResponseDays}天</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">高风险团队</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.highRiskTeams}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">趋势</CardTitle></CardHeader><CardContent><Badge variant={summary.trend === 'up' ? 'destructive' : 'default'}>{summary.trend === 'up' ? '恶化' : '改善'}</Badge></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">管理失职明细</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {details.map((d) => (
              <div key={d.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{d.team}</p>
                  <p className="text-xs text-muted-foreground">红灯{d.redLights}个 / 未处理{d.unresolved}个 / 管理动作{d.managerActions}次</p>
                </div>
                <div className="text-right shrink-0">
                  <Badge variant={d.risk === 'high' ? 'destructive' : 'secondary'}>{d.risk === 'high' ? '高风险' : '中风险'}</Badge>
                  <p className="text-xs text-muted-foreground mt-1">已{d.daysOpen}天</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
