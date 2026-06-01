import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

const mockTrendData = [
  { month: '1月', visits: 18, revenue: 140000, score: 82 },
  { month: '2月', visits: 15, revenue: 125000, score: 78 },
  { month: '3月', visits: 20, revenue: 168000, score: 85 },
  { month: '4月', visits: 22, revenue: 175000, score: 86 },
  { month: '5月', visits: 25, revenue: 192000, score: 88 },
  { month: '6月', visits: 22, revenue: 185000, score: 88 },
]

export default function MyTrend() {
  const [data] = useState(mockTrendData)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">个人趋势</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="visits" stroke="#3b82f6" name="拜访数" strokeWidth={2} />
            <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#10b981" name="营收" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="score" stroke="#f59e0b" name="评分" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
