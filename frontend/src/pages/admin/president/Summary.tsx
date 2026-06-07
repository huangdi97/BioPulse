import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatCard from '@/components/StatCard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { DollarSign, Users, ShieldAlert, CalendarCheck } from 'lucide-react'
import { fetchPresidentSummary } from '@/api/adminPresident'

type SummaryData = Awaited<ReturnType<typeof fetchPresidentSummary>>

export default function Summary() {
  const [data, setData] = useState<SummaryData | null>(null)

  useEffect(() => {
    fetchPresidentSummary().then(setData)
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign className="h-5 w-5 text-green-600" />}
          label="双线汇总（营收）"
          value={data.cardData.totalRevenue}
        />
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-blue-600" />}
          label="拜访数"
          value={data.cardData.totalVisits}
          trend="up"
          trendValue="较上月+22%"
        />
        <StatCard
          icon={<Users className="h-5 w-5 text-purple-600" />}
          label="活跃用户"
          value={data.cardData.activeUsers}
        />
        <StatCard
          icon={<ShieldAlert className="h-5 w-5 text-red-600" />}
          label="合规拦截"
          value={data.cardData.complianceBlocks}
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
            <BarChart data={data.barData}>
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
