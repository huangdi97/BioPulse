import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ComplianceItem {
  id: number
  date: string
  type: string
  result: 'passed' | 'violated' | 'pending'
  detail: string
}

const mockRecords: ComplianceItem[] = [
  { id: 1, date: '2026-05-28', type: '拜访合规检查', result: 'passed', detail: '5月28日拜访华东医院合规检查通过' },
  { id: 2, date: '2026-05-25', type: '话术合规扫描', result: 'passed', detail: '话术内容合规，无违规关键词' },
  { id: 3, date: '2026-05-20', type: '数据真实性核查', result: 'violated', detail: '拜访记录中存在数据不一致情况，需修正' },
  { id: 4, date: '2026-05-15', type: '礼品合规检查', result: 'passed', detail: '礼品登记信息完整，无超限情况' },
  { id: 5, date: '2026-05-10', type: '合规培训', result: 'pending', detail: '待完成合规培训课程' },
]

const resultColors: Record<string, string> = {
  passed: 'bg-green-50 text-green-700 border-green-200',
  violated: 'bg-red-50 text-red-700 border-red-200',
  pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
}

const resultLabels: Record<string, string> = {
  passed: '已通过',
  violated: '已违规',
  pending: '待审核',
}

export default function MyCompliance() {
  const [records] = useState(mockRecords)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">合规记录</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {records.map((r) => (
            <div key={r.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{r.type}</p>
                <p className="text-xs text-muted-foreground">{r.detail}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-muted-foreground">{r.date}</p>
                <Badge className={`text-xs mt-1 ${resultColors[r.result]}`}>
                  {resultLabels[r.result]}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
