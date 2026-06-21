import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AgentInsightBar from '@/components/AgentInsightBar'
import { fetchExpenseWaste } from '@/api/adminPresident'

export default function ExpenseWasteDashboard() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchExpenseWaste>> | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchExpenseWaste().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  const { summary, details } = data

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="president_expense" />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">浪费总金额</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">¥{summary.totalWaste.toLocaleString()}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">违规案例数</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.caseCount}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">平均浪费率</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary.avgRate}%</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">趋势</CardTitle></CardHeader><CardContent><Badge variant={summary.trend === 'up' ? 'destructive' : 'default'}>{summary.trend === 'up' ? '上升' : '下降'}</Badge></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">费用浪费明细</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {details.map((d) => (
              <div key={d.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{d.rep}</p>
                  <p className="text-xs text-muted-foreground">费增{d.expenseUp}% / 访减{d.visitDown}% / 流减{d.flowDown}%</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-medium">¥{d.amount.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">{d.date}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
