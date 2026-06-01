import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { CalendarCheck, Users, Target, AlertTriangle } from 'lucide-react'

const mockStats = {
  totalVisits: 428,
  teamSize: 12,
  coverageRate: 85,
  complianceIssues: 7,
}

const mockWeeklyData = [
  { day: '周一', visits: 18 },
  { day: '周二', visits: 24 },
  { day: '周三', visits: 20 },
  { day: '周四', visits: 28 },
  { day: '周五', visits: 22 },
  { day: '周六', visits: 12 },
  { day: '周日', visits: 8 },
]

export default function TeamStats() {
  const [stats] = useState(mockStats)
  const [weeklyData] = useState(mockWeeklyData)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-blue-600" />}
          label="总拜访数"
          value={stats.totalVisits}
          trend="up"
          trendValue="较上月+12%"
        />
        <StatCard
          icon={<Users className="h-5 w-5 text-green-600" />}
          label="团队人数"
          value={stats.teamSize}
        />
        <StatCard
          icon={<Target className="h-5 w-5 text-purple-600" />}
          label="覆盖率"
          value={stats.coverageRate}
        />
        <StatCard
          icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
          label="违规数"
          value={stats.complianceIssues}
          trend="down"
          trendValue="较上月-3"
        />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">本周拜访趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="visits" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
