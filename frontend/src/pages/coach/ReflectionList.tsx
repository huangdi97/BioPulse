import { useState, useEffect } from 'react'
import { fetchReflections, type Reflection } from '@/api/coach'
import { Card, CardContent } from '@/components/ui/card'
import { BookOpen } from 'lucide-react'

export default function ReflectionList() {
  const [reflections, setReflections] = useState<Reflection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchReflections().then((data) => {
      if (cancelled) return
      setReflections(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-20 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">反思笔记</h2>
      {reflections.map((r) => (
        <Card key={r.id}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium">{r.sessionName}</span>
              <span className="text-xs text-muted-foreground">{r.createdAt}</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{r.content}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
