import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { PIE_COLORS } from '@/mock/adminPresident'
import { fetchPresidentCompliance } from '@/api/adminPresident'

type ComplianceData = Awaited<ReturnType<typeof fetchPresidentCompliance>>

export default function ComplianceOverview() {
  const [data, setData] = useState<ComplianceData | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchPresidentCompliance().then((data) => { if (!cancelled) setData(data) })
    return () => { cancelled = true }
  }, [])

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  const { trendData, categoryData } = data

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">合规趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="violations" stroke="#ef4444" name="违规数" strokeWidth={2} />
              <Line type="monotone" dataKey="processed" stroke="#10b981" name="已处理" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">违规分类分布</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {categoryData.map((_, index) => (
                  <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
