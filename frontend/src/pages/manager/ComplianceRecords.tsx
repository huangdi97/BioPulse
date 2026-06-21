import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Search, AlertTriangle } from 'lucide-react'
import { fetchComplianceRecords } from '@/api/compliance'
import type { ComplianceRecord } from '@/types'

const RISK_LABEL: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
}

const RISK_CLASS: Record<string, string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const STATUS_LABEL: Record<string, string> = {
  pending: '待处理',
  reviewed: '已处理',
  dismissed: '已忽略',
}

const STATUS_CLASS: Record<string, string> = {
  pending: 'bg-orange-100 text-orange-700',
  reviewed: 'bg-green-100 text-green-700',
  dismissed: 'bg-gray-100 text-gray-600',
}

export default function ComplianceRecords() {
  const navigate = useNavigate()
  const [records, setRecords] = useState<ComplianceRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const loadRecords = useCallback(() => {
    setLoading(true)
    const params: { status?: string; riskLevel?: string; repName?: string } = {}
    if (statusFilter !== 'all') params.status = statusFilter
    if (riskFilter !== 'all') params.riskLevel = riskFilter
    if (search.trim()) params.repName = search.trim()
    fetchComplianceRecords(params).then((res) => {
      setRecords(res)
      setLoading(false)
    })
  }, [statusFilter, riskFilter, search])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_compliance_records" />
      <div className="flex gap-3 flex-wrap items-center">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索代表姓名..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-8 pr-3 rounded-md border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="all">全部风险</option>
          <option value="critical">严重</option>
          <option value="high">高风险</option>
          <option value="medium">中风险</option>
          <option value="low">低风险</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="all">全部状态</option>
          <option value="pending">待处理</option>
          <option value="reviewed">已处理</option>
          <option value="dismissed">已忽略</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
          加载中...
        </div>
      ) : records.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <AlertTriangle className="h-10 w-10 mb-2 opacity-30" />
            <span className="text-sm">暂无违规记录</span>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {records.map((record) => (
            <Card
              key={record.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/manager/compliance/records/${record.id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-xs text-muted-foreground shrink-0 min-w-[100px]">
                    {record.createdAt}
                  </span>
                  <span className="text-sm font-medium">{record.repName}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${RISK_CLASS[record.riskLevel]}`}
                  >
                    {RISK_LABEL[record.riskLevel]}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-muted text-muted-foreground">
                    {record.keyword}
                  </span>
                  <span className="text-xs text-muted-foreground">{record.category}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ml-auto ${STATUS_CLASS[record.status]}`}
                  >
                    {STATUS_LABEL[record.status]}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-2 line-clamp-1">
                  {record.content}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
