import { useState, useEffect } from 'react'
import { fetchFunnel, type FunnelStage } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { Filter } from 'lucide-react'

const STAGE_COLORS = [
  'bg-blue-400', 'bg-cyan-400', 'bg-teal-400', 'bg-green-400', 'bg-emerald-400',
]

export default function FunnelView() {
  const [funnel, setFunnel] = useState<FunnelStage[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchFunnel().then((data) => {
      if (cancelled) return
      setFunnel(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-4"><div className="h-64 bg-muted rounded-xl animate-pulse" /></div>

  const maxCount = Math.max(...funnel.map((s) => s.count), 1)

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold flex items-center gap-2"><Filter className="h-5 w-5 text-amber-600" />销售漏斗</h2>
      <Card>
        <CardContent className="pt-4">
          <div className="space-y-4">
            {funnel.map((stage, idx) => (
              <div key={stage.stage} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{stage.stage}</span>
                  <span className="text-muted-foreground">{stage.count}个 · {stage.amount}</span>
                </div>
                <div className="bg-muted rounded-full h-8">
                  <div
                    className={`h-8 rounded-full ${STAGE_COLORS[idx % STAGE_COLORS.length]} flex items-center justify-center`}
                    style={{ width: `${Math.max(8, (stage.count / maxCount) * 100)}%` }}
                  >
                    <span className="text-sm text-white font-medium">{stage.count}</span>
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
