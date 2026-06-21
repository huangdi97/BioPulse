import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchHcps, type HcpQueryParams } from '@/api/hcps'
import type { HCP } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'
import AgentInsightBar from '@/components/AgentInsightBar'
import { MapPin, Building2, Star, User } from 'lucide-react'

const DEPT_OPTIONS = [
  { value: '全部', label: '全部科室' },
  { value: '心内科', label: '心内科' },
  { value: '内分泌科', label: '内分泌科' },
  { value: '消化内科', label: '消化内科' },
  { value: '呼吸科', label: '呼吸科' },
  { value: '神经内科', label: '神经内科' },
]

const REGION_OPTIONS = [
  { value: '全部', label: '全部地区' },
  { value: '北京', label: '北京' },
  { value: '上海', label: '上海' },
  { value: '广州', label: '广州' },
  { value: '杭州', label: '杭州' },
]

const PRIORITY_OPTIONS = [
  { value: '全部', label: '全部优先级' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

function priorityBadge(priority: HCP['priority']): {
  color: string
  label: string
  icon: React.ReactNode
} {
  switch (priority) {
    case 'high':
      return {
        color: 'text-red-500 bg-red-50 border-red-200',
        label: '高',
        icon: <Star className="h-3 w-3 fill-red-500 text-red-500" />,
      }
    case 'medium':
      return {
        color: 'text-blue-500 bg-blue-50 border-blue-200',
        label: '中',
        icon: <Star className="h-3 w-3 fill-blue-500 text-blue-500" />,
      }
    case 'low':
      return {
        color: 'text-gray-400 bg-gray-50 border-gray-200',
        label: '低',
        icon: <Star className="h-3 w-3 fill-gray-400 text-gray-400" />,
      }
  }
}

export default function HcpList() {
  const navigate = useNavigate()
  const [hcps, setHcps] = useState<HCP[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [dept, setDept] = useState('全部')
  const [region, setRegion] = useState('全部')
  const [priority, setPriority] = useState('全部')

  const loadHcps = useCallback(async (params: HcpQueryParams) => {
    setLoading(true)
    const data = await fetchHcps(params)
    setHcps(data)
    setLoading(false)
  }, [])

  useEffect(() => {
    loadHcps({})
  }, [loadHcps])

  useEffect(() => {
    const timer = setTimeout(() => {
      loadHcps({
        search: search || undefined,
        dept: dept === '全部' ? undefined : dept,
        region: region === '全部' ? undefined : region,
        priority: priority === '全部' ? undefined : priority,
      })
    }, 200)
    return () => clearTimeout(timer)
  }, [search, dept, region, priority, loadHcps])

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="rep_hcp_list" />
      <SearchBar placeholder="搜索姓名或医院..." value={search} onChange={setSearch} />
      <div className="flex gap-2 flex-wrap">
        <FilterDropdown label="科室" value={dept} options={DEPT_OPTIONS} onChange={setDept} />
        <FilterDropdown label="地区" value={region} options={REGION_OPTIONS} onChange={setRegion} />
        <FilterDropdown label="优先级" value={priority} options={PRIORITY_OPTIONS} onChange={setPriority} />
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-40" />
                  </div>
                  <Skeleton className="h-6 w-10 rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : hcps.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <User className="h-12 w-12 mb-3 opacity-30" />
          <p className="text-sm">未找到匹配的客户</p>
          <p className="text-xs mt-1">请尝试调整搜索条件</p>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {hcps.map((hcp) => {
              const badge = priorityBadge(hcp.priority)
              return (
                <Card
                  key={hcp.id}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => navigate(`/rep/hcps/${hcp.id}`)}
                >
                  <CardContent className="p-3 flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold">{hcp.name}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                        <Building2 className="h-3 w-3" />
                        <span>{hcp.hospital}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span>{hcp.dept}</span>
                        <span>·</span>
                        <MapPin className="h-3 w-3" />
                        <span>{hcp.region}</span>
                        <span>·</span>
                        <span>上次: {hcp.lastVisit}</span>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${badge.color}`}
                    >
                      {badge.icon}
                      {badge.label}
                    </span>
                  </CardContent>
                </Card>
              )
            })}
          </div>
          <p className="text-center text-xs text-muted-foreground">
            共 {hcps.length} 位客户
          </p>
        </>
      )}
    </div>
  )
}
