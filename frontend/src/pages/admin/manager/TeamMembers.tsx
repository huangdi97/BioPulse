import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { fetchManagerMembers } from '@/api/adminManager'
import type { Member } from '@/api/adminManager'

export default function TeamMembers() {
  const [members, setMembers] = useState<Member[]>([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchManagerMembers().then(setMembers)
  }, [])

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
