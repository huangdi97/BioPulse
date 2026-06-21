import { useState, useEffect, useMemo } from 'react'
import { fetchCoachStats } from '@/api/coach'
import StatCard from '@/components/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Play, CheckCircle2, Star, TrendingUp, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/Skeleton'
import { exportToJSON } from '@/utils/export'

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

  const exportData = useMemo(() => [{
    总演练场次: stats.totalSessions,
    完成场次: stats.completedSessions,
    平均得分: stats.averageScore,
    技能提升率: `${stats.improvementRate}%`,
    累计练习时长: `${stats.totalDuration}分钟`,
  }], [stats])

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-24" />
        <div className="flex gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="flex-1 h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-32 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="coach_stats" />
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">数据统计</h2>
        <div className="flex-1" />
        <Button variant="outline" size="sm" onClick={() => exportToJSON(exportData, '演练统计.json')}>
          <Download className="h-4 w-4 mr-1" />导出JSON
        </Button>
      </div>
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
