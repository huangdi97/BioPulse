import { useState, useEffect } from 'react'
import { fetchBiddings, type Bidding } from '@/api/opportunity-api'
import { Card, CardContent } from '@/components/ui/card'
import { FileText, Calendar, Clock } from 'lucide-react'

const STATUS_MAP: Record<Bidding['status'], { label: string; color: string }> = {
  preparing: { label: '准备中', color: 'bg-blue-50 text-blue-700' },
  submitted: { label: '已提交', color: 'bg-yellow-50 text-yellow-700' },
  won: { label: '中标', color: 'bg-green-50 text-green-700' },
  lost: { label: '未中标', color: 'bg-red-50 text-red-700' },
}

export default function BiddingList() {
  const [biddings, setBiddings] = useState<Bidding[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchBiddings().then((data) => {
      if (cancelled) return
      setBiddings(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-20 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">投标管理</h2>
      {biddings.map((b) => {
        const status = STATUS_MAP[b.status]
        return (
          <Card key={b.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold">{b.title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />截止: {b.deadline}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />{b.createdAt}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="text-sm font-bold">{b.amount}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>{status.label}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
