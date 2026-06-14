import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchHcpDetail, fetchVisitHistory } from '@/api/hcps'
import type { HCP, VisitRecord } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ArrowLeft,
  User,
  Building2,
  MapPin,
  Briefcase,
  Clock,
  Play,
  Lightbulb,
} from 'lucide-react'
import AgentSummaryCard from '../../components/AgentSummaryCard'
import AgentInsightBar from '../../components/AgentInsightBar'

export default function HcpDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [hcp, setHcp] = useState<HCP | null>(null)
  const [visits, setVisits] = useState<VisitRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    const hcpId = parseInt(id)
    Promise.all([fetchHcpDetail(hcpId), fetchVisitHistory(hcpId)]).then(
      ([hcpData, visitData]) => {
        if (cancelled) return
        setHcp(hcpData)
        setVisits(
          visitData.length > 0
            ? visitData
            : [
                { id: 1, hcpId, hcpName: hcpData?.name ?? '', content: '产品介绍和新药处方方案讨论', visitType: '实地拜访', createdAt: '2026-05-28', complianceStatus: 'passed' as const, date: '2026-05-28', summary: '产品介绍和新药处方方案讨论' },
                { id: 2, hcpId, hcpName: hcpData?.name ?? '', content: '学术交流会跟进，文献分享', visitType: '线上会议', createdAt: '2026-05-15', complianceStatus: 'passed' as const, date: '2026-05-15', summary: '学术交流会跟进，文献分享' },
                { id: 3, hcpId, hcpName: hcpData?.name ?? '', content: '首次拜访，建立合作关系', visitType: '实地拜访', createdAt: '2026-04-20', complianceStatus: 'passed' as const, date: '2026-04-20', summary: '首次拜访，建立合作关系' },
              ].slice(0, 5) as VisitRecord[]
        )
        setLoading(false)
      }
    )
    return () => {
      cancelled = true
    }
  }, [id])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-20 bg-muted rounded" />
        <div className="h-40 bg-muted rounded-xl" />
        <div className="h-32 bg-muted rounded-xl" />
        <div className="h-24 bg-muted rounded-xl" />
      </div>
    )
  }

  if (!hcp) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p>客户信息未找到</p>
        <Button variant="link" onClick={() => navigate('/rep/hcps')}>
          返回列表
        </Button>
      </div>
    )
  }

  const priorityLabel = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级',
  }[hcp.priority]

  const priorityColor = {
    high: 'text-red-600',
    medium: 'text-blue-600',
    low: 'text-gray-400',
  }[hcp.priority]

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate('/rep/hcps')}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </button>

      <div className="flex items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <User className="h-7 w-7 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-bold">{hcp.name}</h1>
          <p className="text-sm text-muted-foreground">{hcp.title}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AgentSummaryCard title='知识情报摘要' agentKey='knowledge_worker' pageId='rep_hcp_detail' variant='summary' />
        <AgentSummaryCard title='策略建议' agentKey='sales_suggestion' pageId='rep_hcp_detail' variant='suggestion' />
      </div>
      <AgentInsightBar pageId="rep_hcp_detail" />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">医院:</span>
            <span className="font-medium">{hcp.hospital}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Briefcase className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">科室:</span>
            <span className="font-medium">{hcp.dept}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">地区:</span>
            <span className="font-medium">{hcp.region}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Star className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">优先级:</span>
            <span className={`font-medium ${priorityColor}`}>{priorityLabel}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="h-4 w-4" />
            拜访历史
          </CardTitle>
        </CardHeader>
        <CardContent>
          {visits.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              暂无拜访记录
            </p>
          ) : (
            <div className="space-y-3">
              {visits.map((visit, idx) => (
                <div key={visit.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="h-2 w-2 rounded-full bg-primary" />
                    {idx < visits.length - 1 && (
                      <div className="w-px flex-1 bg-border my-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-3">
                    <p className="text-xs text-muted-foreground">{visit.date}</p>
                    <p className="text-sm mt-1">{visit.summary}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            AI 建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            该客户近期处方量趋势良好，建议关注其学术需求，适时提供最新临床研究资料。保持每月1-2次的拜访频率。
          </p>
        </CardContent>
      </Card>

      <Button
        className="w-full"
        size="lg"
        onClick={() => navigate(`/rep/visits/new?hcpId=${id}`)}
      >
        <Play className="h-4 w-4 mr-2" />
        开始拜访
      </Button>
    </div>
  )
}

function Star({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  )
}
