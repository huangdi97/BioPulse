import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Filter, Calendar, User, Building2 } from 'lucide-react'
import { mockOpportunities } from '@/mock/manager'
import type { Opportunity, OpportunityStage } from '@/types'

const STAGE_LABELS: Record<OpportunityStage, string> = {
  lead: '初步接触',
  follow_up: '跟进中',
  negotiation: '商务谈判',
  closed_won: '已赢单',
}

const STAGE_BARS: { stage: OpportunityStage; color: string; bg: string; text: string }[] = [
  { stage: 'lead', color: 'bg-blue-400', bg: 'bg-blue-50', text: 'text-blue-700' },
  { stage: 'follow_up', color: 'bg-yellow-400', bg: 'bg-yellow-50', text: 'text-yellow-700' },
  { stage: 'negotiation', color: 'bg-orange-400', bg: 'bg-orange-50', text: 'text-orange-700' },
  { stage: 'closed_won', color: 'bg-green-400', bg: 'bg-green-50', text: 'text-green-700' },
]

const STAGE_TAG: Record<OpportunityStage, string> = {
  lead: 'bg-blue-50 text-blue-700',
  follow_up: 'bg-yellow-50 text-yellow-700',
  negotiation: 'bg-orange-50 text-orange-700',
  closed_won: 'bg-green-50 text-green-700',
}

export default function ManagerOpportunities() {
  const [opportunities] = useState<Opportunity[]>(mockOpportunities)

  const stageCounts: Record<OpportunityStage, number> = {
    lead: 0,
    follow_up: 0,
    negotiation: 0,
    closed_won: 0,
  }
  opportunities.forEach((o) => {
    stageCounts[o.stage]++
  })

  const total = opportunities.length || 1

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="h-4 w-4" />
            阶段漏斗
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {STAGE_BARS.map(({ stage, color, bg, text }) => (
              <div key={stage} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${bg} ${text}`}>
                    {STAGE_LABELS[stage]}
                  </span>
                  <span className="text-sm font-semibold">{stageCounts[stage]}</span>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${color}`}
                    style={{ width: `${Math.max(8, (stageCounts[stage] / total) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-2">
        {opportunities.map((opp) => (
          <Card key={opp.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <p className="text-sm font-semibold truncate">{opp.title}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Building2 className="h-3 w-3" />
                    <span>{opp.hospital}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {opp.owner}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {opp.expectedClose}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span className="text-sm font-bold text-foreground">{opp.amount}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STAGE_TAG[opp.stage]}`}
                  >
                    {STAGE_LABELS[opp.stage]}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
