import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  resultColors,
  resultLabels,
} from '@/mock/adminEmployee'
import { fetchEmployeeCompliance } from '@/api/adminEmployee'
import type { ComplianceItem } from '@/api/adminEmployee'

export default function MyCompliance() {
  const [records, setRecords] = useState<ComplianceItem[]>([])

  useEffect(() => {
    fetchEmployeeCompliance().then(setRecords)
  }, [])

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
