import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import AgentInsightBar from '@/components/AgentInsightBar'
import { CalendarCheck, DollarSign, TrendingUp, Star } from 'lucide-react'
import { fetchEmployeePerformance } from '@/api/adminEmployee'

export default function MyPerformance() {
  const [perf, setPerf] = useState<{ monthlyVisits: number; monthlyRevenue: number; growth: number; score: number }>({
    monthlyVisits: 0,
    monthlyRevenue: 0,
    growth: 0,
    score: 0,
  })
  const [details, setDetails] = useState<Array<{ label: string; value: string }>>([])

  useEffect(() => {
    fetchEmployeePerformance().then((data) => {
      setPerf(data.perf)
      setDetails(data.details)
    })
  }, [])

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="employee_performance" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-blue-600" />}
          label="本月拜访"
          value={perf.monthlyVisits}
        />
        <StatCard
          icon={<DollarSign className="h-5 w-5 text-green-600" />}
          label="本月营收"
          value={perf.monthlyRevenue}
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
          label="业绩增长"
          value={perf.growth}
        />
        <StatCard
          icon={<Star className="h-5 w-5 text-yellow-600" />}
          label="综合评分"
          value={perf.score}
        />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">绩效详情</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {details.map((d) => (
              <div key={d.label} className="text-center p-4 rounded-lg bg-muted/50">
                <p className="text-2xl font-bold mb-1">{d.value}</p>
                <p className="text-sm text-muted-foreground">{d.label}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
