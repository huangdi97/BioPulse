import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchOpportunities, type OppRecord } from '@/api/opportunity-api'
import { Card, CardContent } from '@/components/ui/card'
import { Building2, User, Calendar, Filter } from 'lucide-react'

const STAGE_LABELS: Record<OppRecord['stage'], string> = {
  lead: '初步接触',
  follow_up: '跟进中',
  negotiation: '商务谈判',
  closed_won: '已赢单',
}

const STAGE_TAG: Record<OppRecord['stage'], string> = {
  lead: 'bg-blue-50 text-blue-700',
  follow_up: 'bg-yellow-50 text-yellow-700',
  negotiation: 'bg-orange-50 text-orange-700',
  closed_won: 'bg-green-50 text-green-700',
}

export default function OpportunityList() {
  const navigate = useNavigate()
  const [opportunities, setOpportunities] = useState<OppRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchOpportunities().then((data) => {
      if (cancelled) return
      setOpportunities(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2, 3, 4].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-20 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-lg font-semibold">商机列表</h2>
      </div>
      <div className="space-y-2">
        {opportunities.map((opp) => (
          <Card
            key={opp.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/opportunity/opportunities/${opp.id}`)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <p className="text-sm font-semibold truncate">{opp.title}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Building2 className="h-3 w-3" /><span>{opp.hospital}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><User className="h-3 w-3" />{opp.owner}</span>
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{opp.expectedClose}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span className="text-sm font-bold">{opp.amount}</span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STAGE_TAG[opp.stage]}`}>
                    {STAGE_LABELS[opp.stage]}
                  </span>
                  <span className="text-xs text-muted-foreground">{opp.probability}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
