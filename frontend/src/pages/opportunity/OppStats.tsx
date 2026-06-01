import { useState, useEffect } from 'react'
import { fetchOppStats } from '@/api/opportunity-api'
import StatCard from '@/components/StatCard'
import { Target, TrendingUp, BarChart3, CheckCircle2 } from 'lucide-react'

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

  if (loading) {
    return <div className="space-y-4 animate-pulse"><div className="flex gap-4">{[1, 2, 3].map((i) => <div key={i} className="flex-1 h-24 bg-muted rounded-xl" />)}</div></div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">统计数据</h2>
      <div className="flex gap-4">
        <StatCard icon={<Target className="h-5 w-5 text-purple-600" />} label="商机总数" value={(stats.total as number) ?? 0} />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-blue-600" />} label="进行中" value={(stats.active as number) ?? 0} />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-green-600" />} label="赢单率" value={(stats.winRate as number) ?? 0} />
      </div>
    </div>
  )
}
