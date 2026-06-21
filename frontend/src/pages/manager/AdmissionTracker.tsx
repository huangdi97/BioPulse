import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import AgentInsightBar from '@/components/AgentInsightBar'
import { fetchAdmissions, createAdmission, updateAdmissionStatus } from '@/api/admission'
import { mockAdmissions } from '@/mock/admission'
import { Plus, Loader2, ChevronRight } from 'lucide-react'
import type { AdmissionRecord } from '@/types'

const STATUS_FLOW = ['待提交', '药事会排期', '审批中', '已通过', '已驳回']

const STATUS_COLOR: Record<string, string> = {
  '待提交': 'bg-slate-100 text-slate-600 border-slate-200',
  '药事会排期': 'bg-blue-100 text-blue-700 border-blue-200',
  '审批中': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  '已通过': 'bg-green-100 text-green-700 border-green-200',
  '已驳回': 'bg-red-100 text-red-700 border-red-200',
}

export default function AdmissionTracker() {
  const [records, setRecords] = useState<AdmissionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ hospital_name: '', department: '', product: '', notes: '' })
  const [submitting, setSubmitting] = useState(false)

  const load = () => {
    setLoading(true)
    fetchAdmissions()
      .then(setRecords)
      .catch(() => setRecords(mockAdmissions))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchAdmissions()
      .then((data) => { if (!cancelled) setRecords(data) })
      .catch(() => { if (!cancelled) setRecords(mockAdmissions) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const handleCreate = async () => {
    if (!form.hospital_name || !form.product) return
    setSubmitting(true)
    try {
      await createAdmission(form)
      setForm({ hospital_name: '', department: '', product: '', notes: '' })
      setShowForm(false)
      load()
    } catch {
      const newRecord: AdmissionRecord = {
        id: Date.now(),
        hospital_name: form.hospital_name,
        department: form.department,
        product: form.product,
        status: '待提交',
        meeting_date: null,
        notes: form.notes,
        rep_name: '当前用户',
        created_at: new Date().toISOString().slice(0, 10),
      }
      setRecords((prev) => [newRecord, ...prev])
      setShowForm(false)
      setForm({ hospital_name: '', department: '', product: '', notes: '' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleAdvance = async (id: number, currentStatus: string) => {
    const idx = STATUS_FLOW.indexOf(currentStatus)
    if (idx < 0 || idx >= STATUS_FLOW.length - 1) return
    const nextStatus = STATUS_FLOW[idx + 1]
    try {
      await updateAdmissionStatus(id, nextStatus)
      load()
    } catch {
      setRecords((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: nextStatus } : r))
      )
    }
  }

  const activeStatuses = STATUS_FLOW.slice(0, -1)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_admission" />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">入院进度看板</h1>
        <Button size="sm" onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4 mr-1" />
          新建入院
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">新建入院记录</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <input
                className="px-3 py-2 border rounded-md text-sm"
                placeholder="医院名称 *"
                value={form.hospital_name}
                onChange={(e) => setForm({ ...form, hospital_name: e.target.value })}
              />
              <input
                className="px-3 py-2 border rounded-md text-sm"
                placeholder="科室"
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
              />
              <input
                className="px-3 py-2 border rounded-md text-sm"
                placeholder="产品名称 *"
                value={form.product}
                onChange={(e) => setForm({ ...form, product: e.target.value })}
              />
              <input
                className="px-3 py-2 border rounded-md text-sm"
                placeholder="备注"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </div>
            <div className="flex gap-2 mt-3">
              <Button size="sm" onClick={handleCreate} loading={submitting}>提交</Button>
              <Button size="sm" variant="outline" onClick={() => setShowForm(false)}>取消</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {records.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
            暂无入院记录
          </CardContent>
        </Card>
      ) : (
        records.map((r) => {
          const statusIdx = STATUS_FLOW.indexOf(r.status)
          const isEnd = r.status === '已通过' || r.status === '已驳回'
          return (
            <Card key={r.id}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-sm">{r.hospital_name}</h3>
                    <p className="text-xs text-muted-foreground">
                      {r.department} · {r.product}
                    </p>
                  </div>
                  <Badge className={STATUS_COLOR[r.status] || ''}>{r.status}</Badge>
                </div>

                {!isEnd && (
                  <div className="flex items-center gap-1 mb-3">
                    {activeStatuses.slice(0, statusIdx + 1).map((s, i) => (
                      <div key={s} className="flex items-center gap-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          i === statusIdx
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {s}
                        </span>
                        {i < activeStatuses.length - 1 && (
                          <ChevronRight className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {r.status === '已驳回' && (
                  <div className="flex items-center gap-1 mb-3">
                    {STATUS_FLOW.map((s, i) => (
                      <div key={s} className="flex items-center gap-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          i <= statusIdx
                            ? 'bg-red-100 text-red-700'
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {s}
                        </span>
                        {i < STATUS_FLOW.length - 1 && (
                          <ChevronRight className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {r.status === '已通过' && (
                  <div className="flex items-center gap-1 mb-3">
                    {STATUS_FLOW.map((s, i) => (
                      <div key={s} className="flex items-center gap-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          i < statusIdx
                            ? 'bg-green-100 text-green-700'
                            : i === statusIdx
                            ? 'bg-green-600 text-white'
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {s}
                        </span>
                        {i < STATUS_FLOW.length - 1 && (
                          <ChevronRight className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{r.rep_name} · {r.created_at}</span>
                  <div className="flex gap-2">
                    {statusIdx >= 0 && statusIdx < STATUS_FLOW.length - 1 && (
                      <Button size="sm" variant="outline" onClick={() => handleAdvance(r.id, r.status)}>
                        推进至{STATUS_FLOW[statusIdx + 1]}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })
      )}
    </div>
  )
}
