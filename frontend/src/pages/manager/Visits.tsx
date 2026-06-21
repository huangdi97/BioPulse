import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { mockTeamRanking } from '@/mock/manager'
import type { TeamMember } from '@/types'

const REP_OPTIONS = ['全部', '赵建国', '钱晓峰', '孙丽华', '李志远', '周美琴']
const TIME_OPTIONS = ['本周', '上周', '本月', '上月']

const WEEKLY_TREND = [
  { day: '周一', visits: 18 },
  { day: '周二', visits: 22 },
  { day: '周三', visits: 25 },
  { day: '周四', visits: 20 },
  { day: '周五', visits: 24 },
  { day: '周六', visits: 12 },
  { day: '周日', visits: 7 },
]

function FilterDropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (v: string) => void
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        className="flex items-center gap-1 h-9 px-3 rounded-md border border-input bg-background text-sm hover:bg-accent hover:text-accent-foreground"
      >
        <span className="text-muted-foreground">{label}:</span>
        <span className="font-medium">{value}</span>
        <svg className="h-3 w-3 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 min-w-[100px] rounded-md border bg-popover shadow-md">
          {options.map((opt) => (
            <button
              key={opt}
              type="button"
              onMouseDown={() => {
                onChange(opt)
                setOpen(false)
              }}
              className={`w-full text-left px-3 py-1.5 text-sm hover:bg-accent rounded-sm ${
                value === opt ? 'font-medium bg-accent' : ''
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ManagerVisits() {
  const [rep, setRep] = useState('全部')
  const [timeRange, setTimeRange] = useState('本周')
  const [ranking] = useState<TeamMember[]>(mockTeamRanking)

  const filteredRanking =
    rep === '全部' ? ranking : ranking.filter((m) => m.name === rep)

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_visits" />
      <div className="flex gap-2 flex-wrap">
        <FilterDropdown label="代表" value={rep} options={REP_OPTIONS} onChange={setRep} />
        <FilterDropdown label="时间范围" value={timeRange} options={TIME_OPTIONS} onChange={setTimeRange} />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">本周每日拜访趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={WEEKLY_TREND} margin={{ top: 4, left: -20, right: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="visits" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">代表详情</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-4 py-2 font-medium text-muted-foreground">姓名</th>
                  <th className="text-right px-4 py-2 font-medium text-muted-foreground">拜访数</th>
                  <th className="text-right px-4 py-2 font-medium text-muted-foreground">覆盖率</th>
                  <th className="text-right px-4 py-2 font-medium text-muted-foreground">合规率</th>
                  <th className="text-right px-4 py-2 font-medium text-muted-foreground">商机数</th>
                </tr>
              </thead>
              <tbody>
                {filteredRanking.map((member) => (
                  <tr key={member.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">{member.name}</td>
                    <td className="text-right px-4 py-3">{member.visitCount}</td>
                    <td className="text-right px-4 py-3">{member.coverage}%</td>
                    <td className="text-right px-4 py-3">
                      <span
                        className={
                          member.complianceRate >= 95
                            ? 'text-green-600'
                            : member.complianceRate >= 90
                              ? 'text-yellow-600'
                              : 'text-red-600'
                        }
                      >
                        {member.complianceRate}%
                      </span>
                    </td>
                    <td className="text-right px-4 py-3">{member.opportunityCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
