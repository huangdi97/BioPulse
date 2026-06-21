import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/contexts/ToastContext'
import AgentInsightBar from '@/components/AgentInsightBar'
import client from '@/api/client'
import type { DraftItem, DraftListResponse } from '@/api/visits'
import { FileText, CheckCircle2, Clock, ArrowLeft, Save } from 'lucide-react'

export default function VisitDrafts() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [drafts, setDrafts] = useState<DraftItem[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editedFields, setEditedFields] = useState<Record<string, string>>({})

  const userId = localStorage.getItem('user_id') || 'unknown'

  const loadDrafts = useCallback(async () => {
    setLoading(true)
    try {
      const res: DraftListResponse = await client.get('/api/cloud/visit/drafts', { params: { user_id: userId } })
      setDrafts(Array.isArray(res.data) ? res.data : [])
    } catch {
      toast.error('加载草稿列表失败')
    } finally {
      setLoading(false)
    }
  }, [userId, toast])

  useEffect(() => {
    loadDrafts()
  }, [loadDrafts])

  const handleEdit = (draft: DraftItem) => {
    setEditingId(draft.id)
    const fields = draft.extracted_fields
    try {
      const parsed = typeof fields === 'string' ? JSON.parse(fields) : fields || {}
      setEditedFields(Object.fromEntries(Object.entries(parsed).map(([k, v]) => [k, String(v)])))
    } catch {
      setEditedFields({})
    }
  }

  const handleFieldChange = (key: string, value: string) => {
    setEditedFields((prev) => ({ ...prev, [key]: value }))
  }

  const handleConfirm = async (draftId: string) => {
    try {
      await client.post(`/api/cloud/visit/drafts/${draftId}/confirm`, {
        user_id: userId,
        edited_fields: editedFields,
      })
      toast.success('草稿已确认')
      setEditingId(null)
      loadDrafts()
    } catch {
      toast.error('确认失败')
    }
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  const truncate = (text: string, max: number) =>
    text && text.length > max ? text.slice(0, max) + '...' : text || ''

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="rep_visit_drafts" />
      <button
        onClick={() => navigate('/rep/visits/new')}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回新建拜访
      </button>

      <h2 className="text-lg font-semibold">拜访草稿</h2>

      {loading && <p className="text-sm text-muted-foreground">加载中...</p>}

      {!loading && drafts.length === 0 && (
        <p className="text-sm text-muted-foreground">暂无草稿</p>
      )}

      <div className="space-y-3">
        {drafts.map((draft) => (
          <Card key={draft.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {draft.status === 'confirmed' ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-yellow-500" />
                  )}
                  <CardTitle className="text-sm font-medium">
                    {draft.status === 'confirmed' ? '已确认' : '草稿'}
                  </CardTitle>
                </div>
                <span className="text-xs text-muted-foreground">{formatDate(draft.created_at)}</span>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">
                <FileText className="inline h-3 w-3 mr-1" />
                {truncate(draft.transcript, 100)}
              </p>

              {editingId === draft.id ? (
                <div className="space-y-2 border rounded-md p-3 bg-gray-50">
                  {Object.entries(editedFields).map(([key, val]) => (
                    <div key={key} className="flex gap-2 items-center">
                      <label className="text-sm font-medium min-w-[80px]">{key}:</label>
                      <input
                        type="text"
                        value={val}
                        onChange={(e) => handleFieldChange(key, e.target.value)}
                        className="flex-1 rounded border border-input bg-background px-2 py-1 text-sm"
                      />
                    </div>
                  ))}
                  <Button size="sm" className="mt-2" onClick={() => handleConfirm(draft.id)}>
                    <Save className="h-3 w-3 mr-1" />
                    确认草稿
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  {draft.status === 'draft' && (
                    <Button size="sm" variant="outline" onClick={() => handleEdit(draft)}>
                      编辑并确认
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
