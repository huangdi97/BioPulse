import { useState } from 'react'
import StatCard from '@/components/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CalendarCheck, Users, Target, AlertTriangle, Trophy } from 'lucide-react'
import { mockTeamSummary, mockTeamRanking, mockOpportunities } from '@/mock/manager'
import type { OpportunityStage } from '@/types'

const STAGE_LABELS: Record<OpportunityStage, string> = {
  lead: '初步接触',
  follow_up: '跟进中',
  negotiation: '商务谈判',
  closed_won: '已赢单',
}

const STAGE_ORDER: OpportunityStage[] = ['lead', 'follow_up', 'negotiation', 'closed_won']

const STAGE_COLORS: Record<OpportunityStage, string> = {
  lead: 'text-blue-600',
  follow_up: 'text-yellow-600',
  negotiation: 'text-orange-600',
  closed_won: 'text-green-600',
}

const STAGE_BG: Record<OpportunityStage, string> = {
  lead: 'bg-blue-50',
  follow_up: 'bg-yellow-50',
  negotiation: 'bg-orange-50',
  closed_won: 'bg-green-50',
}

export default function ManagerDashboard() {
  const [summary] = useState(mockTeamSummary)
  const [ranking] = useState(mockTeamRanking)
  const [opportunities] = useState(mockOpportunities)

  const stageCounts: Record<OpportunityStage, number> = {
    lead: 0,
    follow_up: 0,
    negotiation: 0,
    closed_won: 0,
  }
  opportunities.forEach((o) => {
    stageCounts[o.stage]++
  })

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-blue-600" />}
          label="总拜访数"
          value={summary.totalVisits}
          trend={summary.visitsTrend}
          trendValue={summary.visitsTrendValue}
        />
        <StatCard
          icon={<Users className="h-5 w-5 text-green-600" />}
          label="团队人数"
          value={summary.teamSize}
        />
        <StatCard
          icon={<Target className="h-5 w-5 text-purple-600" />}
          label="覆盖率"
          value={summary.coverageRate}
        />
        <StatCard
          icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
          label="违规数"
          value={summary.complianceIssues}
          trend="down"
          trendValue="较上月-1"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Trophy className="h-4 w-4 text-yellow-500" />
              拜访排行 TOP5
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {ranking.map((member, index) => (
                <div
                  key={member.id}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 ${
                      index === 0
                        ? 'bg-yellow-100 text-yellow-700'
                        : index === 1
                          ? 'bg-gray-100 text-gray-600'
                          : index === 2
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium flex-1">{member.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {member.visitCount}次
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {member.coverage}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" />
              商机概览
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {STAGE_ORDER.map((stage) => (
                <div key={stage} className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STAGE_BG[stage]} ${STAGE_COLORS[stage]}`}
                  >
                    {STAGE_LABELS[stage]}
                  </span>
                  <div className="flex-1 bg-muted rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        stage === 'lead'
                          ? 'bg-blue-400'
                          : stage === 'follow_up'
                            ? 'bg-yellow-400'
                            : stage === 'negotiation'
                              ? 'bg-orange-400'
                              : 'bg-green-400'
                      }`}
                      style={{
                        width: `${Math.max(
                          8,
                          (stageCounts[stage] / (opportunities.length || 1)) * 100
                        )}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold w-6 text-right">
                    {stageCounts[stage]}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
