import { useState, useEffect, useMemo } from 'react'
import { fetchNotes, type NoteItem } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { StickyNote, Clock, User } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const DATE_OPTIONS = [
  { value: '全部', label: '全部时间' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'older', label: '更早' },
]

function isWithinDays(dateStr: string, days: number): boolean {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  return diff <= days * 24 * 60 * 60 * 1000
}

export default function NoteList() {
  const [notes, setNotes] = useState<NoteItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [dateFilter, setDateFilter] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchNotes().then((data) => {
      if (cancelled) return
      setNotes(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return notes.filter((n) => {
      const matchSearch = !search || n.title.includes(search) || n.content.includes(search) || n.relatedTo.includes(search)
      let matchDate = true
      if (dateFilter === 'week') matchDate = isWithinDays(n.createdAt, 7)
      else if (dateFilter === 'month') matchDate = isWithinDays(n.createdAt, 30)
      return matchSearch && matchDate
    })
  }, [notes, search, dateFilter])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-24 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">笔记</h2>
      <SearchBar placeholder="搜索标题、内容或相关对象..." value={search} onChange={setSearch} />
      <FilterDropdown label="时间" value={dateFilter} options={DATE_OPTIONS} onChange={setDateFilter} />
      {filtered.map((note) => (
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
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的笔记</div>
      )}
    </div>
  )
}
