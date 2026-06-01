import { useState, useEffect, useMemo } from 'react'
import { fetchOppStats } from '@/api/opportunity-api'
import StatCard from '@/components/StatCard'
import { Target, TrendingUp, BarChart3, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/Skeleton'
import { exportToCSV } from '@/utils/export'

export default function OppStats() {
  const [stats, setStats] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchOppStats().then((data) => {
      if (cancelled) return
      setStats(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const exportData = useMemo(() => [{
    '商机总数': stats.total,
    '进行中': stats.active,
    '总金额': stats.totalAmount,
    '平均概率': `${stats.avgProbability}%`,
    '赢单率': `${stats.winRate}%`,
  }], [stats])

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-24" />
        <div className="flex gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="flex-1 h-24 rounded-xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">统计数据</h2>
        <div className="flex-1" />
        <Button variant="outline" size="sm" onClick={() => exportToCSV(exportData, '商机统计.csv')}>
          <Download className="h-4 w-4 mr-1" />导出CSV
        </Button>
      </div>
      <div className="flex gap-4">
        <StatCard icon={<Target className="h-5 w-5 text-purple-600" />} label="商机总数" value={(stats.total as number) ?? 0} />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-blue-600" />} label="进行中" value={(stats.active as number) ?? 0} />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-green-600" />} label="赢单率" value={(stats.winRate as number) ?? 0} />
      </div>
    </div>
  )
}
