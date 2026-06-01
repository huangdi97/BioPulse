import { useState, useEffect } from 'react'
import { fetchNotes, type NoteItem } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { StickyNote, Clock, User } from 'lucide-react'

export default function NoteList() {
  const [notes, setNotes] = useState<NoteItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchNotes().then((data) => {
      if (cancelled) return
      setNotes(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-24 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">笔记</h2>
      {notes.map((note) => (
        <Card key={note.id}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-amber-100">
                <StickyNote className="h-4 w-4 text-amber-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{note.title}</p>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{note.content}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><User className="h-3 w-3" />{note.relatedTo}</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{note.createdAt}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
