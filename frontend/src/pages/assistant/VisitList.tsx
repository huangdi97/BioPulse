import { useState, useEffect } from 'react'
import { fetchVisits, type VisitRecord } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Calendar, User } from 'lucide-react'

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  passed: { label: '通过', color: 'bg-green-50 text-green-700' },
  violated: { label: '违规', color: 'bg-red-50 text-red-700' },
  pending: { label: '待审', color: 'bg-yellow-50 text-yellow-700' },
}

export default function VisitList() {
  const [visits, setVisits] = useState<VisitRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchVisits().then((data) => {
      if (cancelled) return
      setVisits(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-16 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="assistant_visits" />
      <h2 className="text-lg font-semibold">拜访记录</h2>
      <div className="space-y-2">
        {visits.map((v) => {
          const status = STATUS_MAP[v.complianceStatus] ?? STATUS_MAP.pending
          return (
            <Card key={v.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{v.hcpName}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{v.summary}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{v.date}</span>
                      <span>{v.visitType}</span>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>{status.label}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
