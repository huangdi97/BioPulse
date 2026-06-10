import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, FileText } from 'lucide-react'
import client, { getApiUrl } from '@/api/client'

export default function InspectionHistory() {
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [auditTrail, setAuditTrail] = useState<any[] | null>(null)
  const [auditLoading, setAuditLoading] = useState(false)

  useEffect(() => {
    client.get(getApiUrl('cloud', '/api/inspection/history')).then(res => {
      setHistory((res as any[]) || [])
    }).finally(() => setLoading(false))
  }, [])

  async function handleExpand(inspectionId: string) {
    if (expandedId === inspectionId) {
      setExpandedId(null)
      setAuditTrail(null)
      return
    }
    setExpandedId(inspectionId)
    setAuditLoading(true)
    try {
      const res = await client.get(getApiUrl('cloud', `/api/inspection/${inspectionId}/audit-trail`))
      setAuditTrail((res as any)?.trail || (res as any[]) || [])
    } catch {
      setAuditTrail([])
    }
    setAuditLoading(false)
  }

  if (loading) return <p className="text-sm text-muted-foreground py-8 text-center">加载中...</p>

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">飞检历史记录</h2>
        <p className="text-sm text-muted-foreground">历史检查记录与CAPA审计轨迹</p>
      </div>

      {history.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center">暂无历史记录</p>
      ) : (
        <div className="space-y-3">
          {history.map((record: any) => {
            const inspectionId = record.inspection_id || record.id
            return (
              <Card key={inspectionId}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between cursor-pointer" onClick={() => handleExpand(inspectionId)}>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                        <p className="text-sm font-medium truncate">{record.title || record.name || `检查 ${inspectionId}`}</p>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span>{record.date || record.created_at || '-'}</span>
                        <span>得分: {record.score ?? '-'}</span>
                        <span>状态: {record.status || record.result || '-'}</span>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="shrink-0">
                      {expandedId === inspectionId ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                  </div>

                  {expandedId === inspectionId && (
                    <div className="mt-3 pt-3 border-t space-y-3">
                      <h4 className="text-xs font-semibold text-muted-foreground">审计轨迹</h4>
                      {auditLoading ? (
                        <p className="text-xs text-muted-foreground">加载审计轨迹...</p>
                      ) : auditTrail && auditTrail.length > 0 ? (
                        <div className="space-y-2">
                          {auditTrail.map((step: any, i: number) => (
                            <div key={step.id || i} className="flex gap-3 text-xs">
                              <div className="flex flex-col items-center">
                                <div className="w-2 h-2 rounded-full bg-primary shrink-0" />
                                {i < auditTrail.length - 1 && <div className="w-px flex-1 bg-border" />}
                              </div>
                              <div className="pb-3">
                                <p className="font-medium">{step.stage || step.what || '-'}</p>
                                <p className="text-muted-foreground">{step.who} | {step.when || '-'}</p>
                                {step.evidence && <p className="text-muted-foreground">证据: {step.evidence}</p>}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">无审计轨迹数据</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
