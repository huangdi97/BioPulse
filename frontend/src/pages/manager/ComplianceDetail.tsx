import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import AgentInsightBar from '@/components/AgentInsightBar'
import { ArrowLeft, CheckCircle, XCircle, ShieldCheck } from 'lucide-react'
import { fetchComplianceRecordDetail, fetchAuditChain, scanContent } from '@/api/compliance'
import type { ComplianceRecord, AuditEntry, Violation } from '@/types'

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

export default function ComplianceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [record, setRecord] = useState<ComplianceRecord | null>(null)
  const [auditChain, setAuditChain] = useState<AuditEntry[]>([])
  const [violations, setViolations] = useState<Violation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    const numId = parseInt(id, 10)
    fetchComplianceRecordDetail(numId).then((res) => {
      setRecord(res)
      if (res) {
        const scan = scanContent(res.content)
        scan.then((result) => setViolations(result.violations))
        fetchAuditChain('compliance_record', res.id).then(setAuditChain)
      }
      setLoading(false)
    })
  }, [id])

  const handleMarkReviewed = () => {
    if (record) {
      setRecord({ ...record, status: 'reviewed', reviewedAt: new Date().toISOString() })
    }
  }

  const handleMarkDismissed = () => {
    if (record) {
      setRecord({ ...record, status: 'dismissed', reviewedAt: new Date().toISOString() })
    }
  }

  if (loading || !record) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        加载中...
      </div>
    )
  }

  const highlightViolation = (text: string): React.ReactNode => {
    if (!violations.length) return text
    const regex = new RegExp(
      `(${violations.map((v) => v.keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
      'g'
    )
    const parts = text.split(regex)
    return parts.map((part, i) =>
      violations.some((v) => v.keyword === part) ? (
        <span key={i} className="bg-red-200 text-red-900 px-0.5 rounded">
          {part}
        </span>
      ) : (
        part
      )
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_compliance_detail" />
      <button
        type="button"
        onClick={() => navigate('/manager/compliance/records')}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </button>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">代表</span>
              <p className="font-medium">{record.repName}</p>
            </div>
            <div>
              <span className="text-muted-foreground">时间</span>
              <p className="font-medium">{record.createdAt}</p>
            </div>
            <div>
              <span className="text-muted-foreground">风险等级</span>
              <p>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${RISK_CLASS[record.riskLevel]}`}
                >
                  {RISK_LABEL[record.riskLevel]}
                </span>
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">状态</span>
              <p>
                <span className="text-sm font-medium">
                  {STATUS_LABEL[record.status] ?? '待处理'}
                </span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">拜访内容原文</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {highlightViolation(record.content)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">扫描结果</CardTitle>
        </CardHeader>
        <CardContent>
          {violations.length === 0 ? (
            <p className="text-sm text-muted-foreground">未检测到违规内容</p>
          ) : (
            <div className="space-y-3">
              {violations.map((v, idx) => (
                <div key={idx} className="rounded-lg border p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">{v.category}</span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${RISK_CLASS[v.riskLevel] ?? 'bg-muted text-muted-foreground'}`}
                    >
                      {RISK_LABEL[v.riskLevel] ?? v.riskLevel}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    建议修改：{v.suggestion}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {record.status === 'pending' && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">审核操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <Button
                onClick={handleMarkReviewed}
                className="inline-flex items-center gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                标记已处理
              </Button>
              <Button
                variant="outline"
                onClick={handleMarkDismissed}
                className="inline-flex items-center gap-2"
              >
                <XCircle className="h-4 w-4" />
                标记为误报
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-blue-500" />
            审计链
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative pl-6 border-l-2 border-muted space-y-6">
            {auditChain.map((entry, idx) => (
              <div key={idx} className="relative">
                <div
                  className={`absolute -left-[25px] top-0 h-4 w-4 rounded-full border-2 ${
                    entry.verified
                      ? 'bg-green-100 border-green-500'
                      : 'bg-gray-100 border-gray-400'
                  }`}
                />
                <p className="text-xs text-muted-foreground">{entry.timestamp}</p>
                <p className="text-sm font-medium">{entry.action}</p>
                <p className="text-sm text-muted-foreground">{entry.actor}</p>
                <span
                  className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                    entry.verified
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {entry.verified ? '已验证' : '待验证'}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
