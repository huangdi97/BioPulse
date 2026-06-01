import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

interface Member {
  id: number
  name: string
  role: string
  visits: number
  coverage: number
  compliance: number
  status: 'active' | 'inactive'
}

const mockMembers: Member[] = [
  { id: 1, name: '赵建国', role: '销售代表', visits: 24, coverage: 92, compliance: 96, status: 'active' },
  { id: 2, name: '钱晓峰', role: '销售代表', visits: 21, coverage: 88, compliance: 100, status: 'active' },
  { id: 3, name: '孙丽华', role: '销售代表', visits: 18, coverage: 85, compliance: 94, status: 'active' },
  { id: 4, name: '李志远', role: '销售代表', visits: 16, coverage: 78, compliance: 88, status: 'active' },
  { id: 5, name: '周美琴', role: '销售代表', visits: 14, coverage: 80, compliance: 92, status: 'active' },
  { id: 6, name: '吴国强', role: '销售代表', visits: 12, coverage: 72, compliance: 85, status: 'inactive' },
  { id: 7, name: '郑丽萍', role: '销售代表', visits: 10, coverage: 68, compliance: 90, status: 'active' },
]

export default function TeamMembers() {
  const [members] = useState(mockMembers)
  const [search, setSearch] = useState('')

  const filtered = members.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">成员列表</CardTitle>
          <Input
            placeholder="搜索成员..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left py-2 px-2">姓名</th>
                <th className="text-left py-2 px-2">角色</th>
                <th className="text-right py-2 px-2">拜访数</th>
                <th className="text-right py-2 px-2">覆盖率</th>
                <th className="text-right py-2 px-2">合规率</th>
                <th className="text-center py-2 px-2">状态</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m) => (
                <tr key={m.id} className="border-b hover:bg-muted/50">
                  <td className="py-2 px-2 font-medium">{m.name}</td>
                  <td className="py-2 px-2 text-muted-foreground">{m.role}</td>
                  <td className="py-2 px-2 text-right">{m.visits}</td>
                  <td className="py-2 px-2 text-right">{m.coverage}%</td>
                  <td className="py-2 px-2 text-right">{m.compliance}%</td>
                  <td className="py-2 px-2 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      m.status === 'active'
                        ? 'bg-green-50 text-green-700'
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      {m.status === 'active' ? '在职' : '离职'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
