import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchOpportunities, type OppRecord } from '@/api/opportunity-api'
import { Card, CardContent } from '@/components/ui/card'
import { Building2, User, Calendar, Download, ArrowUpDown } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'
import { Button } from '@/components/ui/button'
import { exportToCSV, exportToJSON } from '@/utils/export'

const STAGE_LABELS: Record<OppRecord['stage'], string> = {
  lead: '初步接触',
  follow_up: '跟进中',
  negotiation: '商务谈判',
  closed_won: '已赢单',
}

const STAGE_TAG: Record<OppRecord['stage'], string> = {
  lead: 'bg-blue-50 text-blue-700',
  follow_up: 'bg-yellow-50 text-yellow-700',
  negotiation: 'bg-orange-50 text-orange-700',
  closed_won: 'bg-green-50 text-green-700',
}

const STAGE_OPTIONS = [
  { value: '全部', label: '全部阶段' },
  { value: 'lead', label: '初步接触' },
  { value: 'follow_up', label: '跟进中' },
  { value: 'negotiation', label: '商务谈判' },
  { value: 'closed_won', label: '已赢单' },
]

const SORT_OPTIONS = [
  { value: 'default', label: '默认排序' },
  { value: 'amount_desc', label: '金额从高到低' },
  { value: 'amount_asc', label: '金额从低到高' },
  { value: 'date_desc', label: '预计成交最近' },
]

function parseAmount(a: string): number {
  return parseInt(a.replace(/[^0-9]/g, '')) || 0
}

export default function OpportunityList() {
  const navigate = useNavigate()
  const [opportunities, setOpportunities] = useState<OppRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [stage, setStage] = useState('全部')
  const [sort, setSort] = useState('default')

  useEffect(() => {
    let cancelled = false
    fetchOpportunities().then((data) => {
      if (cancelled) return
      setOpportunities(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    let result = opportunities.filter((o) => {
      const matchSearch = !search || o.title.includes(search) || o.hospital.includes(search) || o.owner.includes(search)
      const matchStage = stage === '全部' || o.stage === stage
      return matchSearch && matchStage
    })

    switch (sort) {
      case 'amount_desc':
        result = [...result].sort((a, b) => parseAmount(b.amount) - parseAmount(a.amount))
        break
      case 'amount_asc':
        result = [...result].sort((a, b) => parseAmount(a.amount) - parseAmount(b.amount))
        break
      case 'date_desc':
        result = [...result].sort((a, b) => new Date(b.expectedClose).getTime() - new Date(a.expectedClose).getTime())
        break
    }

    return result
  }, [opportunities, search, stage, sort])

  const exportColumns = [
    { key: 'title' as keyof OppRecord, title: '商机名称' },
    { key: 'hospital' as keyof OppRecord, title: '医院' },
    { key: 'amount' as keyof OppRecord, title: '金额' },
    { key: 'stage' as keyof OppRecord, title: '阶段' },
    { key: 'owner' as keyof OppRecord, title: '负责人' },
    { key: 'probability' as keyof OppRecord, title: '概率(%)' },
    { key: 'expectedClose' as keyof OppRecord, title: '预计成交' },
  ]

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-20 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">商机列表</h2>
        <div className="flex-1" />
        <Button variant="outline" size="sm" onClick={() => exportToCSV(filtered, '商机列表.csv', exportColumns)}>
          <Download className="h-4 w-4 mr-1" />导出CSV
        </Button>
        <Button variant="outline" size="sm" onClick={() => exportToJSON(filtered, '商机列表.json')}>
          <Download className="h-4 w-4 mr-1" />导出JSON
        </Button>
      </div>
      <SearchBar placeholder="搜索商机名称、医院或负责人..." value={search} onChange={setSearch} />
      <div className="flex gap-2 flex-wrap">
        <FilterDropdown label="阶段" value={stage} options={STAGE_OPTIONS} onChange={setStage} />
        <FilterDropdown label="排序" value={sort} options={SORT_OPTIONS} onChange={setSort} />
      </div>
      <div className="space-y-2">
        {filtered.map((opp) => (
          <Card
            key={opp.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/opportunity/opportunities/${opp.id}`)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <p className="text-sm font-semibold truncate">{opp.title}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Building2 className="h-3 w-3" /><span>{opp.hospital}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><User className="h-3 w-3" />{opp.owner}</span>
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{opp.expectedClose}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span className="text-sm font-bold">{opp.amount}</span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STAGE_TAG[opp.stage]}`}>
                    {STAGE_LABELS[opp.stage]}
                  </span>
                  <span className="text-xs text-muted-foreground">{opp.probability}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的商机</div>
      )}
    </div>
  )
}
