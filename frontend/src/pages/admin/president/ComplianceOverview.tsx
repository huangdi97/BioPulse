import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'

const mockTrendData = [
  { month: '1月', violations: 12, processed: 8 },
  { month: '2月', violations: 10, processed: 7 },
  { month: '3月', violations: 15, processed: 11 },
  { month: '4月', violations: 8, processed: 6 },
  { month: '5月', violations: 6, processed: 5 },
  { month: '6月', violations: 4, processed: 4 },
]

const mockCategoryData = [
  { name: '话术违规', value: 35 },
  { name: '竞品提及', value: 25 },
  { name: '数据造假', value: 18 },
  { name: '礼品超限', value: 12 },
  { name: '其他', value: 10 },
]

const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6']

export default function ComplianceOverview() {
  const [trendData] = useState(mockTrendData)
  const [categoryData] = useState(mockCategoryData)

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
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
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
