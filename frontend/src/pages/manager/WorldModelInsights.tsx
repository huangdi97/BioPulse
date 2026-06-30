import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronRight, Brain, Network, Clock } from 'lucide-react'

interface WorldModelInsight {
  summary: string
  agent_key: string
  agents: string[]
  confidence: number
  timestamp: string
  supporting_evidence: Record<string, any>
}

const AGENT_LABELS: Record<string, string> = {
  compliance_monitor: '合规监测',
  anomaly_analysis: '异常分析',
  opportunity_scanner: '商机扫描',
  sales_suggestion: '销售策略',
  sales_coach_analyst: '销售教练',
  knowledge_worker: '知识维护',
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return ts }
}

function confidenceColor(c: number): string {
  if (c >= 0.8) return 'bg-green-100 text-green-800 border-green-300'
  if (c >= 0.5) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
  return 'bg-red-100 text-red-800 border-red-300'
}

export default function WorldModelInsights() {
  const [insights, setInsights] = useState<WorldModelInsight[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch('/api/v1/agent/insights?page=world_model')
      .then((res) => { if (!res.ok) throw new Error(); return res.json() })
      .then((data) => {
        if (cancelled) return
        const raw = Array.isArray(data.insights) ? data.insights : []
        const mapped: WorldModelInsight[] = raw.map((ins: any) => ({
          summary: ins.summary || ins.insight_text || '',
          agent_key: ins.agent_key || '',
          agents: ins.agents || (ins.agent_key ? [ins.agent_key] : []),
          confidence: ins.confidence ?? 0,
          timestamp: ins.timestamp || '',
          supporting_evidence: ins.supporting_evidence || ins.details || {},
        }))
        setInsights(mapped.slice(0, 20))
        setLoading(false)
      })
      .catch(() => { if (!cancelled) { setInsights([]); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx); else next.add(idx)
      return next
    })
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          世界模型洞察
        </h1>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-md bg-[var(--clr-gray-20)]" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          世界模型洞察
        </h1>
        <Badge variant="outline">{insights.length} 条认知</Badge>
      </div>

      {insights.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
            暂无世界模型认知数据
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {insights.map((ins, idx) => {
            const open = expanded.has(idx)
            const evidence = Object.entries(ins.supporting_evidence)
            return (
              <Card key={idx} className="overflow-hidden">
                <CardHeader
                  className="pb-2 cursor-pointer select-none hover:bg-muted/30 transition-colors"
                  onClick={() => toggle(idx)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {open ? <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />}
                      <CardTitle className="text-sm font-medium truncate">{ins.summary || '(无描述)'}</CardTitle>
                    </div>
                    <Badge className={`text-xs shrink-0 ml-2 ${confidenceColor(ins.confidence)}`}>
                      {(ins.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Brain className="h-3 w-3" />
                      {ins.agents.map((a) => AGENT_LABELS[a] || a).join('、') || '未知'}
                    </span>
                    {ins.timestamp && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatTime(ins.timestamp)}
                      </span>
                    )}
                  </div>
                </CardHeader>
                {open && (
                  <CardContent className="pt-0 pb-3">
                    <div className="border rounded-md divide-y">
                      <div className="px-3 py-1.5 bg-muted/20 text-xs font-medium text-muted-foreground">
                        supporting_evidence ({evidence.length} 项)
                      </div>
                      {evidence.length === 0 ? (
                        <div className="px-3 py-2 text-xs text-muted-foreground">无详细信息</div>
                      ) : (
                        evidence.map(([key, val], ei) => (
                          <div key={ei} className="px-3 py-1.5 flex items-start gap-2 text-xs">
                            <span className="font-mono text-muted-foreground shrink-0 mt-0.5">{key}:</span>
                            <span className="text-foreground break-all">
                              {typeof val === 'object' ? JSON.stringify(val, null, 1) : String(val)}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}