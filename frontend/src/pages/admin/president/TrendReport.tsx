import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

const mockMonthlyData = [
  { month: '1月', revenue: 420000, target: 400000, growth: 5.0 },
  { month: '2月', revenue: 380000, target: 400000, growth: -5.0 },
  { month: '3月', revenue: 510000, target: 450000, growth: 13.3 },
  { month: '4月', revenue: 470000, target: 450000, growth: 4.4 },
  { month: '5月', revenue: 560000, target: 500000, growth: 12.0 },
  { month: '6月', revenue: 509000, target: 500000, growth: 1.8 },
]

export default function TrendReport() {
  const [data] = useState(mockMonthlyData)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">月度业绩趋势</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="revenue" stroke="#3b82f6" name="实际营收" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="target" stroke="#f59e0b" name="目标" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
