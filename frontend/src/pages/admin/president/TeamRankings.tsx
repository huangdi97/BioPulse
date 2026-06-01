import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface TeamRank {
  rank: number
  name: string
  visits: number
  compliance: number
  performance: number
  score: number
}

const mockRankings: TeamRank[] = [
  { rank: 1, name: '华东大区', visits: 245, compliance: 98, performance: 92, score: 96 },
  { rank: 2, name: '华南大区', visits: 218, compliance: 95, performance: 89, score: 92 },
  { rank: 3, name: '华北区域', visits: 196, compliance: 92, performance: 85, score: 88 },
  { rank: 4, name: '华中区域', visits: 175, compliance: 88, performance: 82, score: 84 },
  { rank: 5, name: '西南区域', visits: 152, compliance: 85, performance: 78, score: 80 },
  { rank: 6, name: '西北区域', visits: 128, compliance: 82, performance: 75, score: 76 },
  { rank: 7, name: '东北区域', visits: 110, compliance: 78, performance: 72, score: 72 },
]

export default function TeamRankings() {
  const [rankings] = useState(mockRankings)

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
