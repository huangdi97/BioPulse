import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchAssistantHcpDetail, type AssistantHcp } from '@/api/assistant-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, User, Building2, MapPin } from 'lucide-react'

export default function HcpDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [hcp, setHcp] = useState<AssistantHcp | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    fetchAssistantHcpDetail(parseInt(id)).then((data) => {
      if (cancelled) return
      setHcp(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [id])

  if (loading) return <div className="space-y-4 animate-pulse"><div className="h-6 w-20 bg-muted rounded" /><div className="h-40 bg-muted rounded-xl" /></div>
  if (!hcp) return <div className="flex flex-col items-center justify-center py-16 text-muted-foreground"><p>HCP未找到</p></div>

  return (
    <div className="space-y-4">
      <button onClick={() => navigate('/assistant/hcps')} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" />返回列表
      </button>
      <div className="flex items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-teal-100">
          <User className="h-7 w-7 text-teal-600" />
        </div>
        <div>
          <h1 className="text-xl font-bold">{hcp.name}</h1>
          <p className="text-sm text-muted-foreground">{hcp.title}</p>
        </div>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">基本信息</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-sm"><Building2 className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">医院:</span><span className="font-medium">{hcp.hospital}</span></div>
          <div className="flex items-center gap-2 text-sm"><MapPin className="h-4 w-4 text-muted-foreground" /><span className="text-muted-foreground">科室/地区:</span><span className="font-medium">{hcp.dept} · {hcp.region}</span></div>
        </CardContent>
      </Card>
    </div>
  )
}
