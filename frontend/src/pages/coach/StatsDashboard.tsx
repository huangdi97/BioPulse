import { useState, useEffect } from 'react'
import { fetchCoachStats } from '@/api/coach'
import StatCard from '@/components/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, CheckCircle2, Star, TrendingUp } from 'lucide-react'

export default function StatsDashboard() {
  const [stats, setStats] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchCoachStats().then((data) => {
      if (cancelled) return
      setStats(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-4 animate-pulse"><div className="flex gap-4">{[1, 2, 3].map((i) => <div key={i} className="flex-1 h-24 bg-muted rounded-xl" />)}</div></div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">数据统计</h2>
      <div className="flex gap-4">
        <StatCard icon={<Play className="h-5 w-5 text-blue-600" />} label="总演练场次" value={(stats.totalSessions as number) ?? 0} />
        <StatCard icon={<CheckCircle2 className="h-5 w-5 text-green-600" />} label="完成场次" value={(stats.completedSessions as number) ?? 0} />
        <StatCard icon={<Star className="h-5 w-5 text-yellow-600" />} label="平均得分" value={(stats.averageScore as number) ?? 0} />
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><TrendingUp className="h-4 w-4 text-green-500" />进步趋势</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">技能提升率: <span className="font-bold text-green-600">+{(stats.improvementRate as number) ?? 0}%</span></p>
          <p className="text-sm text-muted-foreground mt-1">累计练习时长: <span className="font-bold">{(stats.totalDuration as number) ?? 0}分钟</span></p>
        </CardContent>
      </Card>
    </div>
  )
}
