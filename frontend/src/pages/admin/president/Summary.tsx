import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { DollarSign, Users, ShieldAlert, CalendarCheck } from 'lucide-react'

const mockCardData = {
  totalRevenue: 2850000,
  totalVisits: 1256,
  complianceBlocks: 38,
  activeUsers: 48,
}

const mockBarData = [
  { month: '1月', revenue: 420000, visits: 180 },
  { month: '2月', revenue: 380000, visits: 160 },
  { month: '3月', revenue: 510000, visits: 210 },
  { month: '4月', revenue: 470000, visits: 195 },
  { month: '5月', revenue: 560000, visits: 230 },
  { month: '6月', revenue: 509000, visits: 281 },
]

export default function Summary() {
  const [data] = useState(mockCardData)
  const [barData] = useState(mockBarData)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign className="h-5 w-5 text-green-600" />}
          label="双线汇总（营收）"
          value={data.totalRevenue}
        />
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-blue-600" />}
          label="拜访数"
          value={data.totalVisits}
          trend="up"
          trendValue="较上月+22%"
        />
        <StatCard
          icon={<Users className="h-5 w-5 text-purple-600" />}
          label="活跃用户"
          value={data.activeUsers}
        />
        <StatCard
          icon={<ShieldAlert className="h-5 w-5 text-red-600" />}
          label="合规拦截"
          value={data.complianceBlocks}
          trend="down"
          trendValue="较上月-5%"
        />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">月度营收与拜访趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="revenue" fill="#3b82f6" name="营收 (¥)" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="right" dataKey="visits" fill="#10b981" name="拜访数" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
