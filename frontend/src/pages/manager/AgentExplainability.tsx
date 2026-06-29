import { useState, useEffect, useMemo, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Loader2, ChevronDown, ChevronRight, Brain, CheckCircle2, XCircle, AlertCircle, Search } from 'lucide-react'

interface EvidenceItem {
  key: string
  value: any
}

interface AgentConclusion {
  agent_key: string
  agent_name: string
  summary: string
  details: Record<string, any>
  confidence: number
  page_id: string
  timestamp: string
  evidence: EvidenceItem[]
}

const AGENT_KEYS = [
  'compliance_monitor',
  'anomaly_analysis',
  'opportunity_scanner',
  'sales_suggestion',
  'sales_coach_analyst',
  'knowledge_worker',
]

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  compliance_monitor: '合规监测',
  anomaly_analysis: '异常分析',
  opportunity_scanner: '商机扫描',
  sales_suggestion: '销售策略',
  sales_coach_analyst: '销售教练',
  knowledge_worker: '知识维护',
}

const PAGE_IDS = [
  'manager_dashboard',
  'manager_explainability',
  'compliance_overview',
  'rep_dashboard',
  'president_summary',
  'sa_precall',
  'opportunity_list',
]

function flattenDetails(details: Record<string, any>, prefix = ''): EvidenceItem[] {
  const items: EvidenceItem[] = []
  for (const [key, value] of Object.entries(details)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      items.push(...flattenDetails(value, fullKey))
    } else {
      items.push({ key: fullKey, value })
    }
  }
  return items
}

function confidenceBadge(confidence: number): { color: string; label: string } {
  if (confidence >= 0.8) return { color: 'bg-green-100 text-green-800 border-green-300', label: '高置信度' }
  if (confidence >= 0.5) return { color: 'bg-yellow-100 text-yellow-800 border-yellow-300', label: '中置信度' }
  return { color: 'bg-red-100 text-red-800 border-red-300', label: '低置信度' }
}

export default function AgentExplainability() {
  const [conclusions, setConclusions] = useState<AgentConclusion[]>([])
  const [loading, setLoading] = useState(true)
  const [filterAgent, setFilterAgent] = useState<string>('all')
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [query, setQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    const fetchAll = async () => {
      const results: AgentConclusion[] = []
      for (const pageId of PAGE_IDS) {
        try {
          const res = await fetch(`/api/v1/agent/insights?page=${pageId}`)
          if (!res.ok) continue
          const data = await res.json()
          const insights = data.insights ?? data ?? []
          if (Array.isArray(insights)) {
            for (const ins of insights) {
              results.push({
                agent_key: ins.agent_key || '',
                agent_name: AGENT_DISPLAY_NAMES[ins.agent_key] || ins.agent_key || '未知',
                summary: ins.summary || ins.insight_text || '',
                details: ins.details || {},
                confidence: ins.confidence ?? 0,
                page_id: pageId,
                timestamp: ins.timestamp || new Date().toISOString(),
                evidence: flattenDetails(ins.details || {}),
              })
            }
          }
        } catch {
          // skip failed pages
        }
      }
      if (!cancelled) {
        setConclusions(results)
        setLoading(false)
      }
    }

    fetchAll()
    return () => { cancelled = true }
  }, [])

  const toggleExpand = useCallback((idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx); else next.add(idx)
      return next
    })
  }, [])

  const filtered = useMemo(() => {
    let items = conclusions
    if (filterAgent !== 'all') {
      items = items.filter((c) => c.agent_key === filterAgent)
    }
    if (query.trim()) {
      const q = query.toLowerCase()
      items = items.filter(
        (c) =>
          c.summary.toLowerCase().includes(q) ||
          c.agent_name.toLowerCase().includes(q) ||
          c.evidence.some((e) => e.key.toLowerCase().includes(q) || String(e.value).toLowerCase().includes(q)),
      )
    }
    return items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [conclusions, filterAgent, query])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_explainability" />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          Agent 可解释性
        </h1>
        <Badge variant="outline">{filtered.length} 条结论</Badge>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            className="w-full pl-8 pr-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="搜索结论或证据..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <select
          className="text-sm border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
        >
          <option value="all">全部 Agent</option>
          {AGENT_KEYS.map((k) => (
            <option key={k} value={k}>
              {AGENT_DISPLAY_NAMES[k] || k}
            </option>
          ))}
        </select>
      </div>

      {/* Conclusion Cards */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
            暂无 Agent 结论数据
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((c, idx) => {
            const isExpanded = expanded.has(idx)
            const cb = confidenceBadge(c.confidence)
            return (
              <Card key={idx} className="overflow-hidden">
                <CardHeader
                  className="pb-2 cursor-pointer select-none hover:bg-muted/30 transition-colors"
                  onClick={() => toggleExpand(idx)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                      )}
                      <Badge className="text-xs shrink-0">{c.agent_name}</Badge>
                      <CardTitle className="text-sm font-medium truncate">{c.summary}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <Badge className={`text-xs ${cb.color}`}>{cb.label}</Badge>
                      {c.confidence >= 0.7 ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : c.confidence >= 0.4 ? (
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    page: {c.page_id} &middot; {(c.confidence * 100).toFixed(0)}% 置信度
                  </p>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="pt-2 pb-4">
                    <div className="border rounded-md divide-y">
                      <div className="px-3 py-2 bg-muted/20 text-xs font-medium text-muted-foreground">
                        证据链 ({c.evidence.length} 项)
                      </div>
                      {c.evidence.length === 0 ? (
                        <div className="px-3 py-2 text-xs text-muted-foreground">无详细信息</div>
                      ) : (
                        c.evidence.map((ev, ei) => (
                          <div key={ei} className="px-3 py-2 flex items-start gap-2 text-xs">
                            <span className="font-mono text-muted-foreground shrink-0 mt-0.5">
                              {ev.key}:
                            </span>
                            <span className="text-foreground break-all">
                              {typeof ev.value === 'object' ? JSON.stringify(ev.value) : String(ev.value)}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                    <div className="mt-2 flex justify-end">
                      <Button variant="outline" size="sm" className="text-xs">
                        追问 Agent
                      </Button>
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
