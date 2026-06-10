import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { fetchVisitFraud } from '@/api/adminPresident'

export default function VisitFraudDashboard() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchVisitFraud>> | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchVisitFraud().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  const { summary, details } = data

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">疑似造假数</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.totalFraud}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">涉事代表数</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.caseCount}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">检测率</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.detectionRate}%</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">趋势</CardTitle></CardHeader><CardContent><Badge variant={summary.trend === 'up' ? 'destructive' : 'default'}>{summary.trend === 'up' ? '上升' : '下降'}</Badge></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">拜访造假明细</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {details.map((d) => (
              <div key={d.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{d.rep}</p>
                  <p className="text-xs text-muted-foreground">拜访量增{d.visitsUp}% / 流向持平 / 置信度{Math.round(d.score * 100)}%</p>
                </div>
                <div className="text-right shrink-0">
                  <Badge variant={d.score >= 0.8 ? 'destructive' : 'secondary'}>{d.score >= 0.8 ? '高疑' : '中疑'}</Badge>
                  <p className="text-xs text-muted-foreground mt-1">{d.date}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
