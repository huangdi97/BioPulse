import { useState, useEffect } from 'react'
import { fetchStrategy, type StrategyAdvice } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { Lightbulb, Target, TrendingUp, BarChart3 } from 'lucide-react'

export default function StrategyView() {
  const [strategies, setStrategies] = useState<StrategyAdvice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchStrategy().then((data) => {
      if (cancelled) return
      setStrategies(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-24 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">策略建议</h2>
      {strategies.map((s) => (
        <Card key={s.id}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              <span className="text-sm font-semibold">{s.title}</span>
            </div>
            <div className="space-y-1.5 text-xs text-muted-foreground">
              <div className="flex items-center gap-2"><Target className="h-3 w-3" />目标: {s.target}</div>
              <div className="flex items-center gap-2"><TrendingUp className="h-3 w-3" />方法: {s.approach}</div>
              <div className="flex items-center gap-2"><BarChart3 className="h-3 w-3" />预期: {s.expectedOutcome}</div>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <div className="flex-1 bg-muted rounded-full h-2">
                <div className="h-2 rounded-full bg-amber-500" style={{ width: `${s.confidence}%` }} />
              </div>
              <span className="text-xs font-medium text-amber-600">{s.confidence}%</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
