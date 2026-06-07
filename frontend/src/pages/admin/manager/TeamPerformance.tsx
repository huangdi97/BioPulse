import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { fetchManagerPerformance, type MemberPerf } from '@/api/adminManager'

export default function TeamPerformance() {
  const [data, setData] = useState<MemberPerf[] | null>(null)

  useEffect(() => {
    fetchManagerPerformance().then(setData)
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">成员绩效对比</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="visits" fill="#3b82f6" name="拜访数" radius={[4, 4, 0, 0]} />
            <Bar dataKey="deals" fill="#10b981" name="成交数" radius={[4, 4, 0, 0]} />
            <Bar dataKey="score" fill="#f59e0b" name="绩效分" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
