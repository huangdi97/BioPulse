import { useState, useEffect } from 'react'
import { fetchObjections, type ObjectionItem } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { FileText } from 'lucide-react'

export default function ObjectionList() {
  const [objections, setObjections] = useState<ObjectionItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchObjections().then((data) => {
      if (cancelled) return
      setObjections(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2, 3].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-24 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">异议处理</h2>
      {objections.map((o) => (
        <Card key={o.id}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-red-100">
                <FileText className="h-4 w-4 text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-700">异议: {o.objection}</p>
                <div className="mt-2 p-2 rounded bg-green-50">
                  <p className="text-sm text-green-800">{o.response}</p>
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-muted-foreground">{o.category}</span>
                  <div className="flex items-center gap-1">
                    <div className="w-16 bg-muted rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${o.effectiveness}%` }} />
                    </div>
                    <span className="text-xs text-green-600">{o.effectiveness}%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
