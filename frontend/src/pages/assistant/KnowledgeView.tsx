import { useState, useEffect } from 'react'
import { fetchKnowledge, type KnowledgeItem } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { BookOpen, Clock } from 'lucide-react'

export default function KnowledgeView() {
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchKnowledge().then((data) => {
      if (cancelled) return
      setItems(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2, 3].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-16 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">知识库</h2>
      {items.map((item) => (
        <Card key={item.id}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-teal-100">
                <BookOpen className="h-5 w-5 text-teal-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{item.title}</p>
                <p className="text-xs text-muted-foreground mt-1">{item.summary}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                  <span className="px-1.5 py-0.5 rounded bg-teal-50 text-teal-700">{item.category}</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{item.updatedAt}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
