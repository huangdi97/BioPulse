import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { fetchEmployeeTrend } from '@/api/adminEmployee'

export default function MyTrend() {
  const [data, setData] = useState<Array<{ month: string; visits: number; revenue: number; score: number }>>([])

  useEffect(() => {
    fetchEmployeeTrend().then(setData)
  }, [])

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
