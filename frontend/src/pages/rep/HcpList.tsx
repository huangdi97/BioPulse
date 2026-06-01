import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchHcps, type HcpQueryParams } from '@/api/hcps'
import type { HCP } from '@/types'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Search, ChevronDown, MapPin, Building2, Star, User } from 'lucide-react'

const DEPT_OPTIONS = ['全部', '心内科', '内分泌科', '消化内科', '呼吸科', '神经内科']
const REGION_OPTIONS = ['全部', '北京', '上海', '广州', '杭州']
const PRIORITY_OPTIONS = [
  { value: '全部', label: '全部' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

function FilterDropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[] | { value: string; label: string }[]
  onChange: (v: string) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const displayLabel = getDisplayLabel(value, options)

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 h-9 px-3 rounded-md border border-input bg-background text-sm hover:bg-accent hover:text-accent-foreground"
      >
        <span className="text-muted-foreground">{label}:</span>
        <span className="font-medium">{displayLabel}</span>
        <ChevronDown className="h-3 w-3 text-muted-foreground" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 min-w-[120px] rounded-md border bg-popover shadow-md">
          {Array.isArray(options)
            ? options.map((opt) => {
                const v = typeof opt === 'string' ? opt : opt.value
                const l = typeof opt === 'string' ? opt : opt.label
                return (
                  <button
                    key={v}
                    type="button"
                    onClick={() => {
                      onChange(v)
                      setOpen(false)
                    }}
                    className={`w-full text-left px-3 py-1.5 text-sm hover:bg-accent rounded-sm ${
                      value === v ? 'font-medium bg-accent' : ''
                    }`}
                  >
                    {l}
                  </button>
                )
              })
            : null}
        </div>
      )}
    </div>
  )
}

function getDisplayLabel(
  value: string,
  options: string[] | { value: string; label: string }[]
): string {
  if (typeof options[0] === 'string') {
    return value
  }
  const match = (options as { value: string; label: string }[]).find(
    (o) => o.value === value
  )
  return match?.label ?? value
}

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
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索姓名或医院..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      <div className="flex gap-2 flex-wrap">
        <FilterDropdown
          label="科室"
          value={dept}
          options={DEPT_OPTIONS}
          onChange={setDept}
        />
        <FilterDropdown
          label="地区"
          value={region}
          options={REGION_OPTIONS}
          onChange={setRegion}
        />
        <FilterDropdown
          label="优先级"
          value={priority}
          options={PRIORITY_OPTIONS}
          onChange={setPriority}
        />
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i}>
              <CardContent className="p-4 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-muted" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-24 bg-muted rounded" />
                    <div className="h-3 w-40 bg-muted rounded" />
                  </div>
                  <div className="h-6 w-10 bg-muted rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : hcps.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Search className="h-12 w-12 mb-3 opacity-30" />
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
