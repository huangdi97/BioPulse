import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AgentInsightBar from '@/components/AgentInsightBar'
import { fetchRectification } from '@/api/adminPresident'

const statusLabels: Record<string, string> = { closed: '已闭环', in_progress: '整改中', overdue: '已逾期' }
const statusColors: Record<string, string> = { closed: 'bg-green-50 text-green-700 border-green-200', in_progress: 'bg-yellow-50 text-yellow-700 border-yellow-200', overdue: 'bg-red-50 text-red-700 border-red-200' }

export default function RectificationDashboard() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchRectification>> | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchRectification().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  const { summary, details } = data

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="president_rectification" />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">问题总数</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.totalIssues}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">已闭环</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-600">{summary.closed}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">整改中</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-yellow-600">{summary.inProgress}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">闭环率</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.closureRate}%</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">整改闭环明细 (PDCA)</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {details.map((d) => (
              <div key={d.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{d.issue}</p>
                  <p className="text-xs text-muted-foreground">负责人: {d.owner} / 创建: {d.createdAt} / 已{d.days}天</p>
                </div>
                <div className="text-right shrink-0">
                  <Badge className={statusColors[d.status]}>{statusLabels[d.status]}</Badge>
                  {d.closedAt && <p className="text-xs text-muted-foreground mt-1">{d.closedAt}闭环</p>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
