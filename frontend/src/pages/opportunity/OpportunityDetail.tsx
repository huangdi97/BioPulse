import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchOpportunityDetail, type OppRecord } from '@/api/opportunity-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Building2, User, Calendar, Target, BarChart3 } from 'lucide-react'

const STAGE_LABELS: Record<OppRecord['stage'], string> = {
  lead: '初步接触',
  follow_up: '跟进中',
  negotiation: '商务谈判',
  closed_won: '已赢单',
}

export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [opp, setOpp] = useState<OppRecord | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    fetchOpportunityDetail(parseInt(id)).then((data) => {
      if (cancelled) return
      setOpp(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [id])

  if (loading) {
    return <div className="space-y-4 animate-pulse"><div className="h-6 w-20 bg-muted rounded" /><div className="h-40 bg-muted rounded-xl" /></div>
  }

  if (!opp) {
    return <div className="flex flex-col items-center justify-center py-16 text-muted-foreground"><p>商机未找到</p></div>
  }

  return (
    <div className="space-y-4">
      <button onClick={() => navigate('/opportunity/opportunities')} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" />返回列表
      </button>

      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100">
          <Target className="h-6 w-6 text-purple-600" />
        </div>
        <div>
          <h1 className="text-xl font-bold">{opp.title}</h1>
          <p className="text-sm text-muted-foreground">{STAGE_LABELS[opp.stage]}</p>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">基本信息</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-sm"><Building2 className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">医院:</span><span className="font-medium">{opp.hospital}</span></div>
          <div className="flex items-center gap-2 text-sm"><User className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">负责人:</span><span className="font-medium">{opp.owner}</span></div>
          <div className="flex items-center gap-2 text-sm"><Calendar className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">预计关闭:</span><span className="font-medium">{opp.expectedClose}</span></div>
          <div className="flex items-center gap-2 text-sm"><BarChart3 className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">成交率:</span><span className="font-bold text-purple-600">{opp.probability}%</span></div>
          <div className="flex items-center gap-2 text-sm"><Target className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">金额:</span><span className="font-bold">{opp.amount}</span></div>
        </CardContent>
      </Card>
    </div>
  )
}
