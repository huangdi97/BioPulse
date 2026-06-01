import { useState, useEffect } from 'react'
import { fetchPreCall, type PreCallInfo } from '@/api/sales-assistant-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/Skeleton'
import { User, Building2, Lightbulb, ListChecks } from 'lucide-react'

export default function PreCallView() {
  const [info, setInfo] = useState<PreCallInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchPreCall().then((data) => {
      if (cancelled) return
      setInfo(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    )
  }
  if (!info) return <p className="text-muted-foreground">暂无数据</p>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">预呼叫准备</h2>

      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4 text-amber-600" />目标客户</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm font-semibold">{info.hcpName}</p>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            <Building2 className="h-3 w-3" /><span>{info.hospital} · {info.dept}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">上次拜访: {info.lastVisit}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><Lightbulb className="h-4 w-4 text-yellow-500" />拜访建议</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-1.5">
            {info.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-amber-500 mt-1">·</span>{s}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><ListChecks className="h-4 w-4 text-green-500" />关键要点</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-1.5">
            {info.keyPoints.map((p, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-green-500 mt-1">·</span>{p}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
