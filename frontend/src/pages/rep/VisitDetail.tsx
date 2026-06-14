import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchVisitDetail } from '@/api/visits'
import { fetchSuggestions } from '@/api/recommends'
import type { VisitRecord, AiSuggestion } from '@/types'
import { Button } from '@/components/ui/button'
import AiSuggestionCard from '@/components/AiSuggestionCard'
import AgentSummaryCard from '../../components/AgentSummaryCard'
import AgentInsightBar from '../../components/AgentInsightBar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ArrowLeft,
  User,
  Calendar,
  PhoneCall,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Image,
  MapPin,
} from 'lucide-react'

export default function VisitDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [visit, setVisit] = useState<VisitRecord | null>(null)
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    Promise.all([fetchVisitDetail(parseInt(id)), fetchSuggestions()]).then(([visitData, suggestionsData]) => {
      if (cancelled) return
      setVisit(visitData)
      setSuggestions(suggestionsData)
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [id])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-20 bg-muted rounded" />
        <div className="h-28 bg-muted rounded-xl" />
        <div className="h-40 bg-muted rounded-xl" />
        <div className="h-24 bg-muted rounded-xl" />
      </div>
    )
  }

  if (!visit) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p>拜访记录未找到</p>
        <Button variant="link" onClick={() => navigate('/rep/dashboard')}>
          返回看板
        </Button>
      </div>
    )
  }

  const statusConfig = {
    passed: {
      icon: CheckCircle2,
      label: '合规通过',
      color: 'text-green-600',
      bg: 'bg-green-50 border-green-200',
    },
    violated: {
      icon: XCircle,
      label: '存在违规',
      color: 'text-red-600',
      bg: 'bg-red-50 border-red-200',
    },
    pending: {
      icon: Clock,
      label: '待审核',
      color: 'text-yellow-600',
      bg: 'bg-yellow-50 border-yellow-200',
    },
  }[visit.complianceStatus]

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回
      </button>

      <AgentSummaryCard title='拜访分析' agentKey='visit_analysis' pageId='visit_detail' variant='summary' />
      <AgentInsightBar pageId="visit_detail" />

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">拜访详情</CardTitle>
            <span
              className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}
            >
              <statusConfig.icon className="h-3.5 w-3.5" />
              {statusConfig.label}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="text-muted-foreground">客户:</span>
            <span className="font-medium">{visit.hcpName}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="text-muted-foreground">时间:</span>
            <span className="font-medium">{visit.createdAt || visit.date}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <PhoneCall className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="text-muted-foreground">方式:</span>
            <span className="font-medium">{visit.visitType}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">拜访内容</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
            {visit.content || visit.summary}
          </p>
        </CardContent>
      </Card>

      {/* 现场照片 */}
      {visit.evidence_photos && visit.evidence_photos.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Image className="h-4 w-4" />
              现场照片
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-2">
              {visit.evidence_photos.map((url, idx) => (
                <div key={idx} className="aspect-square rounded-md overflow-hidden bg-muted">
                  <img src={url} alt={`现场照片 ${idx+1}`} className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 签到定位 */}
      {visit.location && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              签到定位
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{visit.location}</p>
          </CardContent>
        </Card>
      )}

      {visit.violations && visit.violations.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              合规风险详情
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {visit.violations.map((v, idx) => (
              <div key={idx} className="rounded-md border border-gray-200 bg-gray-50 p-3">
                <p className="text-sm">
                  <span className="font-medium">违规词：</span>
                  <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-mono text-red-700">
                    {v.keyword}
                  </span>
                </p>
                <p className="text-sm mt-1">
                  <span className="font-medium">分类：</span>
                  <span className="text-gray-700">{v.category}</span>
                </p>
                {v.suggestion && (
                  <p className="text-sm mt-1">
                    <span className="font-medium">建议：</span>
                    <span className="text-gray-700">{v.suggestion}</span>
                  </p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <AiSuggestionCard suggestions={suggestions} maxItems={3} />
    </div>
  )
}
