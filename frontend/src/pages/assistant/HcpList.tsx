import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAssistantHcps, type AssistantHcp } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { User, Building2, MapPin } from 'lucide-react'

const PRIORITY_MAP: Record<string, { label: string; color: string }> = {
  high: { label: '高', color: 'bg-red-50 text-red-700' },
  medium: { label: '中', color: 'bg-blue-50 text-blue-700' },
  low: { label: '低', color: 'bg-gray-50 text-gray-500' },
}

export default function HcpList() {
  const navigate = useNavigate()
  const [hcps, setHcps] = useState<AssistantHcp[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchAssistantHcps().then((data) => {
      if (cancelled) return
      setHcps(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2, 3].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-16 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">HCP 列表</h2>
      <div className="space-y-2">
        {hcps.map((hcp) => {
          const prio = PRIORITY_MAP[hcp.priority] ?? PRIORITY_MAP.low
          return (
            <Card
              key={hcp.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/assistant/hcps/${hcp.id}`)}
            >
              <CardContent className="p-3 flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-teal-100">
                  <User className="h-5 w-5 text-teal-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold">{hcp.name}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                    <Building2 className="h-3 w-3" /><span>{hcp.hospital}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                    <span>{hcp.dept}</span><span>·</span><MapPin className="h-3 w-3" /><span>{hcp.region}</span>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${prio.color}`}>{prio.label}</span>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
