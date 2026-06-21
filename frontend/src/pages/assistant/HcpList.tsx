import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAssistantHcps, type AssistantHcp } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { User, Building2, MapPin } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'
import AgentInsightBar from '@/components/AgentInsightBar'

const PRIORITY_MAP: Record<string, { label: string; color: string }> = {
  high: { label: '高', color: 'bg-red-50 text-red-700' },
  medium: { label: '中', color: 'bg-blue-50 text-blue-700' },
  low: { label: '低', color: 'bg-gray-50 text-gray-500' },
}

const PRIORITY_OPTIONS = [
  { value: '全部', label: '全部优先级' },
  { value: 'high', label: '高优先级' },
  { value: 'medium', label: '中优先级' },
  { value: 'low', label: '低优先级' },
]

export default function HcpList() {
  const navigate = useNavigate()
  const [hcps, setHcps] = useState<AssistantHcp[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [priority, setPriority] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchAssistantHcps().then((data) => {
      if (cancelled) return
      setHcps(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return hcps.filter((h) => {
      const matchSearch = !search || h.name.includes(search) || h.hospital.includes(search) || h.dept.includes(search)
      const matchPri = priority === '全部' || h.priority === priority
      return matchSearch && matchPri
    })
  }, [hcps, search, priority])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-16 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="assistant_hcp_list" />
      <h2 className="text-lg font-semibold">HCP 列表</h2>
      <SearchBar placeholder="搜索姓名、医院或科室..." value={search} onChange={setSearch} />
      <FilterDropdown label="优先级" value={priority} options={PRIORITY_OPTIONS} onChange={setPriority} />
      <div className="space-y-2">
        {filtered.map((hcp) => {
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
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的客户</div>
      )}
    </div>
  )
}
