import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import { CalendarCheck, DollarSign, TrendingUp, Star } from 'lucide-react'

const mockPerf = {
  monthlyVisits: 22,
  monthlyRevenue: 185000,
  growth: 15,
  score: 88,
  rank: 'A',
}

const mockDetails = [
  { label: '拜访完成率', value: '92%', color: 'text-green-600' },
  { label: '合规通过率', value: '96%', color: 'text-green-600' },
  { label: '客户转化率', value: '23%', color: 'text-blue-600' },
  { label: '任务完成率', value: '85%', color: 'text-yellow-600' },
]

export default function MyPerformance() {
  const [perf] = useState(mockPerf)

  return (
    <div className="space-y-4">
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
            {mockDetails.map((d) => (
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
