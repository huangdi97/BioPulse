import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts'

const mockStatusData = [
  { name: '已通过', value: 156, color: '#10b981' },
  { name: '待审核', value: 23, color: '#f59e0b' },
  { name: '已违规', value: 12, color: '#ef4444' },
]

const mockMemberData = [
  { name: '赵建国', passed: 22, violations: 1 },
  { name: '钱晓峰', passed: 20, violations: 0 },
  { name: '孙丽华', passed: 17, violations: 1 },
  { name: '李志远', passed: 14, violations: 2 },
  { name: '周美琴', passed: 13, violations: 1 },
]

export default function TeamCompliance() {
  const [statusData] = useState(mockStatusData)
  const [memberData] = useState(mockMemberData)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">合规状态分布</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, value }) => `${name} ${value}`}
              >
                {statusData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">成员合规对比</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={memberData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="passed" fill="#10b981" name="已通过" radius={[4, 4, 0, 0]} />
              <Bar dataKey="violations" fill="#ef4444" name="违规" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
