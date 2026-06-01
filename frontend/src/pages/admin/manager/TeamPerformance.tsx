import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

interface MemberPerf {
  name: string
  visits: number
  deals: number
  score: number
}

const mockPerfData: MemberPerf[] = [
  { name: '赵建国', visits: 24, deals: 5, score: 92 },
  { name: '钱晓峰', visits: 21, deals: 3, score: 88 },
  { name: '孙丽华', visits: 18, deals: 4, score: 85 },
  { name: '李志远', visits: 16, deals: 2, score: 78 },
  { name: '周美琴', visits: 14, deals: 1, score: 75 },
]

export default function TeamPerformance() {
  const [data] = useState(mockPerfData)

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
