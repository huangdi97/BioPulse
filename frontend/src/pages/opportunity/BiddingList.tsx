import { useState, useEffect, useMemo } from 'react'
import { fetchBiddings, type Bidding } from '@/api/opportunity-api'
import { Card, CardContent } from '@/components/ui/card'
import { Calendar, Clock } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const STATUS_MAP: Record<Bidding['status'], { label: string; color: string }> = {
  preparing: { label: '准备中', color: 'bg-blue-50 text-blue-700' },
  submitted: { label: '已提交', color: 'bg-yellow-50 text-yellow-700' },
  won: { label: '中标', color: 'bg-green-50 text-green-700' },
  lost: { label: '未中标', color: 'bg-red-50 text-red-700' },
}

const STATUS_OPTIONS = [
  { value: '全部', label: '全部状态' },
  { value: 'preparing', label: '准备中' },
  { value: 'submitted', label: '已提交' },
  { value: 'won', label: '中标' },
  { value: 'lost', label: '未中标' },
]

export default function BiddingList() {
  const [biddings, setBiddings] = useState<Bidding[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchBiddings().then((data) => {
      if (cancelled) return
      setBiddings(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return biddings.filter((b) => {
      const matchSearch = !search || b.title.includes(search) || b.deadline.includes(search)
      const matchStatus = status === '全部' || b.status === status
      return matchSearch && matchStatus
    })
  }, [biddings, search, status])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-20 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">投标管理</h2>
      <SearchBar placeholder="搜索投标名称或截止日期..." value={search} onChange={setSearch} />
      <FilterDropdown label="状态" value={status} options={STATUS_OPTIONS} onChange={setStatus} />
      {filtered.map((b) => {
        const s = STATUS_MAP[b.status]
        return (
          <Card key={b.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold">{b.title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />截止: {b.deadline}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />{b.createdAt}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="text-sm font-bold">{b.amount}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的投标</div>
      )}
    </div>
  )
}
