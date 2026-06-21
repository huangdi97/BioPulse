import { useState, useEffect } from 'react'
import { fetchTrends, type TrendData } from '@/api/opportunity-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { TrendingUp } from 'lucide-react'

export default function TrendsChart() {
  const [trends, setTrends] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchTrends().then((data) => {
      if (cancelled) return
      setTrends(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-4"><div className="h-48 bg-muted rounded-xl animate-pulse" /></div>
  }

  const maxRevenue = Math.max(...trends.map((t) => t.revenue), 1)

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="opp_trends" />
      <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp className="h-5 w-5 text-purple-600" />趋势分析</h2>
      <Card>
        <CardHeader><CardTitle className="text-base">商机营收趋势</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {trends.map((t) => (
              <div key={t.month} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-16">{t.month}</span>
                <div className="flex-1 bg-muted rounded-full h-6 relative">
                  <div
                    className="h-6 rounded-full bg-purple-400 flex items-center justify-end pr-2"
                    style={{ width: `${(t.revenue / maxRevenue) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">{t.revenue}万</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">成交率趋势</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {trends.map((t) => (
              <div key={t.month} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-16">{t.month}</span>
                <div className="flex-1 bg-muted rounded-full h-6 relative">
                  <div
                    className="h-6 rounded-full bg-green-400 flex items-center justify-end pr-2"
                    style={{ width: `${t.winRate}%` }}
                  >
                    <span className="text-xs text-white font-medium">{t.winRate}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
