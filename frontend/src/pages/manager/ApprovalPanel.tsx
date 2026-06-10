import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { fetchPendingApprovals, reviewQuotation } from '@/api/approval'
import { mockApprovals } from '@/mock/approval'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import type { ApprovalRecord } from '@/types'

const STATUS_LABEL: Record<string, string> = {
  pending_approval: '待审批',
  approved: '已通过',
  rejected: '已驳回',
  auto_approved: '自动放行',
}

const STATUS_COLOR: Record<string, string> = {
  pending_approval: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  approved: 'bg-green-100 text-green-700 border-green-200',
  rejected: 'bg-red-100 text-red-700 border-red-200',
  auto_approved: 'bg-blue-100 text-blue-700 border-blue-200',
}

export default function ApprovalPanel() {
  const [records, setRecords] = useState<ApprovalRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchPendingApprovals()
      .then((data) => { if (!cancelled) setRecords(data) })
      .catch(() => { if (!cancelled) setRecords(mockApprovals) })
      .finally(() => setLoading(false))
    return () => { cancelled = true }
  }, [])

  const handleReview = async (id: string, action: 'approve' | 'reject') => {
    setActionId(id)
    try {
      await reviewQuotation(id, action)
      setRecords((prev) => prev.filter((r) => r.quotation_id !== id))
    } catch {
      alert('操作失败，请重试')
    } finally {
      setActionId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">报价审批</h1>
        <Badge className={STATUS_COLOR.pending_approval}>{records.length} 条待审批</Badge>
      </div>

      {records.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
            暂无需审批的报价
          </CardContent>
        </Card>
      ) : (
        records.map((r) => (
          <Card key={r.quotation_id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{r.product}</CardTitle>
                <Badge className={STATUS_COLOR[r.status] || ''}>
                  {STATUS_LABEL[r.status] || r.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                <div>
                  <span className="text-muted-foreground">提交人：</span>
                  <span>{r.rep_name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">报价金额：</span>
                  <span className="font-mono">¥{r.amount.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">额度上限：</span>
                  <span className="font-mono">¥{r.limit_amount.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">超限：</span>
                  <span className={r.amount > r.limit_amount ? 'text-red-600 font-medium' : ''}>
                    ¥{(r.amount - r.limit_amount).toLocaleString()}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-muted-foreground">提交时间：</span>
                  <span>{r.created_at}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleReview(r.quotation_id, 'approve')}
                  loading={actionId === r.quotation_id}
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  通过
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleReview(r.quotation_id, 'reject')}
                  loading={actionId === r.quotation_id}
                >
                  <XCircle className="h-4 w-4 mr-1" />
                  驳回
                </Button>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
