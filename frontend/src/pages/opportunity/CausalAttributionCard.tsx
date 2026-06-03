import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, BarChart3, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import { getOpportunityAttribution, refreshAttribution, type AttributionResponse, type AttributionFactor } from '@/api/opportunity-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/Skeleton'
import { EmptyState } from '@/components/EmptyState'
import { Button } from '@/components/ui/button'

const DIRECTION_LABELS: Record<string, string> = {
  positive: '正面',
  negative: '负面',
}

const FACTOR_DISPLAY_NAMES: Record<string, string> = {
  visit_frequency: '拜访频率',
  product_match: '产品匹配度',
  hcp_relation: 'HCP关系强度',
  competitor_threat: '竞品活动',
  time_window: '时间窗口',
  stage_weight: '阶段权重',
}

type Status = 'loading' | 'ready' | 'error' | 'empty'

interface Props {
  opportunityId: number
}

export default function CausalAttributionCard({ opportunityId }: Props) {
  const [status, setStatus] = useState<Status>('loading')
  const [data, setData] = useState<AttributionResponse | null>(null)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    setStatus('loading')
    setError('')
    try {
      const result = await getOpportunityAttribution(opportunityId)
      setData(result)
      setStatus('ready')
    } catch {
      setData(null)
      setStatus('empty')
    }
  }, [opportunityId])

  useEffect(() => {
    load()
  }, [load])

  const handleRefresh = async () => {
    setRefreshing(true)
    setError('')
    try {
      const result = await refreshAttribution(opportunityId)
      setData(result)
      setStatus('ready')
    } catch (e) {
      setError(e instanceof Error ? e.message : '刷新失败')
    } finally {
      setRefreshing(false)
    }
  }

  const handleAnalyze = async () => {
    setStatus('loading')
    setError('')
    try {
      const result = await refreshAttribution(opportunityId)
      setData(result)
      setStatus('ready')
    } catch {
      setStatus('error')
      setError('归因分析失败，请稍后重试')
    }
  }

  const maxImpact = data
    ? Math.max(...data.factors.map((f) => Math.abs(f.impact)), 1)
    : 1

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          因果归因评分
        </CardTitle>
        {status === 'ready' && (
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-3.5 w-3.5 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? '刷新中...' : '刷新'}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {status === 'loading' && (
          <div className="space-y-3">
            <Skeleton className="h-16 w-32" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 mb-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <p className="text-sm text-muted-foreground mb-3">{error || '加载归因数据失败'}</p>
            <Button size="sm" onClick={handleAnalyze}>重试</Button>
          </div>
        )}

        {status === 'empty' && (
          <EmptyState
            icon={BarChart3}
            title="暂无归因数据"
            description="尚未对该商机进行因果归因分析"
            action="开始分析"
            onAction={handleAnalyze}
          />
        )}

        {status === 'ready' && data && (
          <div className="space-y-4">
            <div className="flex items-end gap-4">
              <div>
                <div className="text-4xl font-bold text-purple-600">
                  {Math.round(data.total_score)}
                </div>
                <div className="text-xs text-muted-foreground mt-1">总分（0-105）</div>
              </div>
              <div className="pb-1">
                <div className="text-lg font-semibold">
                  {Math.round(data.confidence * 100)}%
                </div>
                <div className="text-xs text-muted-foreground">置信度</div>
              </div>
            </div>

            <div className="space-y-2">
              {data.factors.map((factor) => {
                const absImpact = Math.abs(factor.impact)
                const pct = maxImpact > 0 ? (absImpact / maxImpact) * 100 : 0
                const isTop = factor.name === data.top_factor_name
                const isPositive = factor.direction === 'positive'
                return (
                  <div
                    key={factor.name}
                    className={`p-2 rounded-lg border ${isTop ? 'border-purple-300 bg-purple-50' : 'border-border'}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5 text-sm font-medium">
                        {isPositive
                          ? <TrendingUp className="h-3.5 w-3.5 text-green-500" />
                          : <TrendingDown className="h-3.5 w-3.5 text-red-500" />}
                        <span>{FACTOR_DISPLAY_NAMES[factor.name] || factor.name}</span>
                        {isTop && (
                          <span className="text-[10px] bg-purple-200 text-purple-700 px-1.5 py-0.5 rounded-full font-medium">Top</span>
                        )}
                      </div>
                      <span className={`text-sm font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? '+' : ''}{factor.impact}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${isPositive ? 'bg-green-400' : 'bg-red-400'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      {DIRECTION_LABELS[factor.direction]} · 权重 {Math.round(factor.weight * 100)}%
                    </div>
                  </div>
                )
              })}
            </div>

            {data.recommendation && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">{data.recommendation}</p>
              </div>
            )}

            <div className="text-[10px] text-muted-foreground text-right">
              模型版本: {data.model_version}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
