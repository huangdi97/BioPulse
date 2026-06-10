import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { fetchPresidentTrend } from '@/api/adminPresident'

type TrendData = Awaited<ReturnType<typeof fetchPresidentTrend>>

export default function TrendReport() {
  const [data, setData] = useState<TrendData | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchPresidentTrend().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

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
