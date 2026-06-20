import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchSessions, type Session } from '@/api/coach'
import { Card, CardContent } from '@/components/ui/card'
import { Clock, CheckCircle2, PauseCircle, Play } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const STATUS_MAP: Record<Session['status'], { label: string; color: string; icon: typeof Play }> = {
  active: { label: '进行中', color: 'bg-blue-50 text-blue-700', icon: Play },
  completed: { label: '已完成', color: 'bg-green-50 text-green-700', icon: CheckCircle2 },
  paused: { label: '暂停', color: 'bg-yellow-50 text-yellow-700', icon: PauseCircle },
}

const STATUS_OPTIONS = [
  { value: '全部', label: '全部状态' },
  { value: 'active', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'paused', label: '暂停' },
]

export default function SessionList() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchSessions().then((data) => {
      if (cancelled) return
      setSessions(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return sessions.filter((s) => {
      const matchSearch = !search || s.scenarioName.includes(search) || s.createdAt.includes(search)
      const matchStatus = status === '全部' || s.status === status
      return matchSearch && matchStatus
    })
  }, [sessions, search, status])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-16 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">演练记录</h2>
      <SearchBar placeholder="搜索场景名或日期..." value={search} onChange={setSearch} />
      <FilterDropdown label="状态" value={status} options={STATUS_OPTIONS} onChange={setStatus} />
      <div className="space-y-3">
        {filtered.map((session) => {
          const s = STATUS_MAP[session.status]
          const StatusIcon = s.icon
          return (
            <Card
              key={session.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/coach/sessions/${session.id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold">{session.scenarioName}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />{session.createdAt}
                      </span>
                      {session.duration && (
                        <span className="text-xs text-muted-foreground">{session.duration}分钟</span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>
                      <StatusIcon className="h-3 w-3" />{s.label}
                    </span>
                    {session.score != null && (
                      <span className="text-sm font-bold">{session.score}分</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的记录</div>
      )}
    </div>
  )
}
