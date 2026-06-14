import { useState, useEffect, useMemo } from 'react'
import client from '@/api/client'

interface BiddingItem {
  id: number
  title: string
  hospital: string | null
  product_category: string | null
  budget: number | null
  publish_date: string | null
  deadline: string | null
  status: string
  created_at: string | null
}

export default function BiddingMonitor() {
  const [items, setItems] = useState<BiddingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [productFilter, setProductFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  useEffect(() => {
    let cancelled = false
    client.get('/api/opportunity/bidding')
      .then((res) => {
        if (cancelled) return
        const data = res.data
        const list = data?.items ?? data ?? []
        setItems(list)
        setLoading(false)
      })
      .catch(() => {
        if (cancelled) return
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const matchProduct = !productFilter
        || (item.product_category && item.product_category.includes(productFilter))
        || (item.title && item.title.includes(productFilter))
      const matchDateFrom = !dateFrom || !item.publish_date || item.publish_date >= dateFrom
      const matchDateTo = !dateTo || !item.publish_date || item.publish_date <= dateTo
      return matchProduct && matchDateFrom && matchDateTo
    })
  }, [items, productFilter, dateFrom, dateTo])

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">招标价格监控</h2>
        <div className="text-sm text-muted-foreground">加载中...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">招标价格监控</h2>

      <div className="flex flex-wrap gap-3 items-center">
        <input
          className="border rounded px-3 py-1.5 text-sm w-48"
          placeholder="产品名搜索..."
          value={productFilter}
          onChange={(e) => setProductFilter(e.target.value)}
        />
        <input
          type="date"
          className="border rounded px-3 py-1.5 text-sm"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
        />
        <span className="text-sm text-muted-foreground">至</span>
        <input
          type="date"
          className="border rounded px-3 py-1.5 text-sm"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-sm text-muted-foreground">暂无招标数据</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-muted/50 border-b">
                <th className="text-left px-3 py-2 font-medium">招标产品</th>
                <th className="text-left px-3 py-2 font-medium">医院</th>
                <th className="text-right px-3 py-2 font-medium">预算（万元）</th>
                <th className="text-left px-3 py-2 font-medium">状态</th>
                <th className="text-left px-3 py-2 font-medium">发布日期</th>
                <th className="text-left px-3 py-2 font-medium">截止日期</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id} className="border-b hover:bg-muted/30">
                  <td className="px-3 py-2 font-medium">{item.title}</td>
                  <td className="px-3 py-2 text-muted-foreground">{item.hospital || '-'}</td>
                  <td className="px-3 py-2 text-right">
                    {item.budget != null ? (item.budget / 10000).toFixed(1) : '-'}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      item.status === 'won' ? 'bg-green-50 text-green-700'
                      : item.status === 'lost' ? 'bg-red-50 text-red-700'
                      : item.status === 'submitted' ? 'bg-yellow-50 text-yellow-700'
                      : 'bg-blue-50 text-blue-700'
                    }`}>
                      {item.status === 'won' ? '中标'
                      : item.status === 'lost' ? '未中标'
                      : item.status === 'submitted' ? '已提交'
                      : item.status === 'preparing' ? '准备中'
                      : item.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{item.publish_date || '-'}</td>
                  <td className="px-3 py-2 text-muted-foreground">{item.deadline || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
