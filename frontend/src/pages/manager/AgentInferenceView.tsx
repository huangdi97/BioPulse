import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Loader2, Brain, TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react'

interface Scenario {
  id: string
  name: string
  description: string
  variables: string[]
  created_at: string
}

interface CausalNode {
  name: string
  direction: 'up' | 'down' | 'neutral'
  weight: number
}

interface CausalLink {
  from: string
  to: string
  label: string
}

interface Prediction {
  variable: string
  value: number
  unit: string
  confidence: number
  interval_lower: number
  interval_upper: number
}

interface ParallelScenario {
  name: string
  predictions: Prediction[]
}

interface InferenceResult {
  scenario_id: string
  scenario_name: string
  causal_chain: {
    nodes: CausalNode[]
    links: CausalLink[]
  }
  predictions: Prediction[]
  parallel_comparisons: ParallelScenario[]
}

const DIRECTION_ICON: Record<string, typeof TrendingUp> = {
  up: TrendingUp,
  down: TrendingDown,
  neutral: Minus,
}

const DIRECTION_COLOR: Record<string, string> = {
  up: 'text-green-600',
  down: 'text-red-600',
  neutral: 'text-gray-500',
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.5) return 'bg-yellow-500'
  return 'bg-red-500'
}

export default function AgentInferenceView() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<InferenceResult | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/api/v1/inference/scenarios')
      .then((r) => { if (!r.ok) throw new Error() })
      .then((r) => r.json())
      .then((data) => { if (!cancelled) setScenarios(data.scenarios ?? data) })
      .catch(() => { if (!cancelled) setScenarios([]) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const runInference = useCallback(async (scenarioId: string) => {
    setRunning(true)
    setResult(null)
    setSelectedId(scenarioId)
    try {
      const res = await fetch('/api/v1/inference/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setResult(data.result ?? data)
    } catch {
      alert('推演失败，请重试')
    } finally {
      setRunning(false)
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_inference" />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">AI 推演</h1>
        <Badge variant="outline">{scenarios.length} 个场景</Badge>
      </div>

      {/* Scenario Cards Grid */}
      {scenarios.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
            暂无可用场景
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenarios.map((s) => (
            <Card
              key={s.id}
              className={`cursor-pointer transition-all ${
                selectedId === s.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => runInference(s.id)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary" />
                  {s.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p className="text-muted-foreground mb-2">{s.description}</p>
                <div className="flex flex-wrap gap-1">
                  {s.variables.map((v) => (
                    <Badge key={v} variant="secondary" className="text-xs">
                      {v}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Inference Result */}
      {running && (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-5 w-5 animate-spin mr-2 text-muted-foreground" />
          <span className="text-muted-foreground">推演中...</span>
        </div>
      )}

      {result && !running && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold">
            推演结果：{result.scenario_name}
          </h2>

          {/* Causal Chain Visualization */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">因果链</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-2">
                {result.causal_chain.nodes.map((node, i) => {
                  const DirIcon = DIRECTION_ICON[node.direction] || Minus
                  return (
                    <span key={node.name} className="flex items-center gap-1">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-muted text-sm">
                        <DirIcon className={`h-3.5 w-3.5 ${DIRECTION_COLOR[node.direction] || ''}`} />
                        {node.name}
                        <span className="text-xs text-muted-foreground ml-1">
                          ({node.weight.toFixed(2)})
                        </span>
                      </span>
                      {i < result.causal_chain.nodes.length - 1 && (
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      )}
                    </span>
                  )
                })}
              </div>
              {result.causal_chain.links.length > 0 && (
                <div className="mt-3 text-xs text-muted-foreground">
                  {result.causal_chain.links.map((link) => (
                    <div key={`${link.from}-${link.to}`}>
                      {link.from} → {link.to}：{link.label}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Predictions with Confidence & Interval */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {result.predictions.map((p) => (
              <Card key={p.variable}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{p.variable}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-2xl font-bold">
                    {p.value.toFixed(2)}
                    <span className="text-sm font-normal text-muted-foreground ml-1">
                      {p.unit}
                    </span>
                  </div>

                  {/* Confidence Bar */}
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>置信度</span>
                      <span>{(p.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${confidenceColor(p.confidence)}`}
                        style={{ width: `${p.confidence * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Prediction Interval */}
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>预测区间</span>
                    </div>
                    <div className="relative h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="absolute h-full rounded-full bg-blue-300"
                        style={{
                          left: `${((p.interval_lower - (p.value - p.interval_lower)) / ((p.value + p.interval_upper) - (p.value - p.interval_lower))) * 100}%`,
                          width: `${((p.interval_upper - p.interval_lower) / ((p.value + p.interval_upper) - (p.value - p.interval_lower))) * 100}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>{p.interval_lower.toFixed(1)}</span>
                      <span>{p.interval_upper.toFixed(1)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Parallel Comparison */}
          {result.parallel_comparisons.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">平行对比</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 pr-4 font-medium text-muted-foreground">场景</th>
                        {result.predictions.map((p) => (
                          <th key={p.variable} className="text-right py-2 px-2 font-medium text-muted-foreground">
                            {p.variable}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b bg-muted/30">
                        <td className="py-2 pr-4 font-medium">{result.scenario_name}</td>
                        {result.predictions.map((p) => (
                          <td key={p.variable} className="text-right py-2 px-2 font-mono">
                            {p.value.toFixed(2)}
                          </td>
                        ))}
                      </tr>
                      {result.parallel_comparisons.map((pc) => (
                        <tr key={pc.name} className="border-b">
                          <td className="py-2 pr-4">{pc.name}</td>
                          {result.predictions.map((p) => {
                            const match = pc.predictions.find((pp) => pp.variable === p.variable)
                            return (
                              <td key={p.variable} className="text-right py-2 px-2 font-mono">
                                {match ? match.value.toFixed(2) : '-'}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={() => { setResult(null); setSelectedId(null) }}>
              清除结果
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}