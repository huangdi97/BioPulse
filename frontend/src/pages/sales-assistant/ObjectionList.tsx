import { useState, useEffect, useMemo } from 'react'
import { fetchObjections, type ObjectionItem } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { FileText } from 'lucide-react'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const CATEGORY_OPTIONS = [
  { value: '全部', label: '全部分类' },
  { value: '价格', label: '价格' },
  { value: '安全', label: '安全' },
  { value: '习惯', label: '习惯' },
]

const SORT_OPTIONS = [
  { value: 'default', label: '默认排序' },
  { value: 'effectiveness_desc', label: '有效性从高到低' },
  { value: 'effectiveness_asc', label: '有效性从低到高' },
]

export default function ObjectionList() {
  const [objections, setObjections] = useState<ObjectionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('全部')
  const [sort, setSort] = useState('default')

  useEffect(() => {
    let cancelled = false
    fetchObjections().then((data) => {
      if (cancelled) return
      setObjections(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    let result = objections.filter((o) => {
      if (category === '全部') return true
      return o.category === category
    })

    switch (sort) {
      case 'effectiveness_desc':
        result = [...result].sort((a, b) => b.effectiveness - a.effectiveness)
        break
      case 'effectiveness_asc':
        result = [...result].sort((a, b) => a.effectiveness - b.effectiveness)
        break
    }

    return result
  }, [objections, category, sort])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-24 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">异议处理</h2>
      <div className="flex gap-2 flex-wrap">
        <FilterDropdown label="分类" value={category} options={CATEGORY_OPTIONS} onChange={setCategory} />
        <FilterDropdown label="排序" value={sort} options={SORT_OPTIONS} onChange={setSort} />
      </div>
      {filtered.map((o) => (
        <Card key={o.id}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-red-100">
                <FileText className="h-4 w-4 text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-700">异议: {o.objection}</p>
                <div className="mt-2 p-2 rounded bg-green-50">
                  <p className="text-sm text-green-800">{o.response}</p>
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-muted-foreground">{o.category}</span>
                  <div className="flex items-center gap-1">
                    <div className="w-16 bg-muted rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${o.effectiveness}%` }} />
                    </div>
                    <span className="text-xs text-green-600">{o.effectiveness}%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的异议</div>
      )}
    </div>
  )
}
