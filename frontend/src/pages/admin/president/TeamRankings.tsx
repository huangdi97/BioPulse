import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchPresidentRankings, type TeamRank } from '@/api/adminPresident'

export default function TeamRankings() {
  const [rankings, setRankings] = useState<TeamRank[] | null>(null)

  useEffect(() => {
    fetchPresidentRankings().then(setRankings)
  }, [])

  if (!rankings) return <div className="p-4 text-muted-foreground">加载中...</div>

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">团队排名</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left py-2 px-2">排名</th>
                <th className="text-left py-2 px-2">团队</th>
                <th className="text-right py-2 px-2">拜访数</th>
                <th className="text-right py-2 px-2">合规率</th>
                <th className="text-right py-2 px-2">绩效分</th>
                <th className="text-right py-2 px-2">综合得分</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((r) => (
                <tr key={r.rank} className="border-b hover:bg-muted/50">
                  <td className="py-2 px-2">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                      r.rank === 1 ? 'bg-yellow-100 text-yellow-700' :
                      r.rank === 2 ? 'bg-gray-100 text-gray-600' :
                      r.rank === 3 ? 'bg-orange-100 text-orange-700' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {r.rank}
                    </span>
                  </td>
                  <td className="py-2 px-2 font-medium">{r.name}</td>
                  <td className="py-2 px-2 text-right">{r.visits}</td>
                  <td className="py-2 px-2 text-right">{r.compliance}%</td>
                  <td className="py-2 px-2 text-right">{r.performance}</td>
                  <td className="py-2 px-2 text-right font-semibold">{r.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
