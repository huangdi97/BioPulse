import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import AgentInsightBar from '@/components/AgentInsightBar'
import { CheckCircle, XCircle, Clock, Plus } from 'lucide-react'
import { fetchChecklist, createTask } from '@/api/inspection'
import InspectionTaskModal from '@/components/InspectionTaskModal'
import type { InspectionTask, TaskFormData } from '@/types/inspection'

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  passed: { label: '已通过', color: 'text-green-600 bg-green-50' },
  failed: { label: '未通过', color: 'text-red-600 bg-red-50' },
  pending: { label: '待检查', color: 'text-yellow-600 bg-yellow-50' },
}

const CATEGORIES = ['全部', '资质证照', '人员培训', '冷链管理', '样品管理']

export default function InspectionChecklist() {
  const [checklist, setChecklist] = useState<InspectionTask[]>([])
  const [category, setCategory] = useState('全部')
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskResult, setTaskResult] = useState<unknown>(null)

  const loadChecklist = useCallback(() => {
    setLoading(true)
    fetchChecklist(category).then(setChecklist).finally(() => setLoading(false))
  }, [category])

  useEffect(() => { loadChecklist() }, [loadChecklist])

  async function handleCreateTask(data: TaskFormData) {
    const res = await createTask(data)
    setTaskResult(res)
    setShowTaskForm(false)
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_checklist" />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">飞检检查清单</h2>
          <p className="text-sm text-muted-foreground">按类别筛选、查看详情、指派整改</p>
        </div>
        <Button onClick={() => setShowTaskForm(true)}>
          <Plus className="h-4 w-4 mr-1" /> 新建整改任务
        </Button>
      </div>

      <div className="flex gap-2 items-center">
        <Label className="text-sm text-muted-foreground">类别:</Label>
        <div className="flex gap-1">
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                category === c ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground py-8 text-center">加载中...</p>
      ) : checklist.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center">暂无检查项</p>
      ) : (
        <div className="space-y-2">
          {checklist.map((item: InspectionTask) => {
            const statusInfo = STATUS_MAP[item.status || 'pending'] || { label: item.status, color: 'text-gray-600 bg-gray-50' }
            return (
              <Card key={item.id} className="cursor-pointer" onClick={() => setExpandedId(expandedId === String(item.id) ? null : String(item.id))}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.item}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span>{item.category}</span>
                        <span>负责人: {item.assignee}</span>
                        <span>期限: {item.deadline}</span>
                      </div>
                    </div>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${statusInfo.color}`}>
                      {item.status === 'passed' ? <CheckCircle className="h-3 w-3" /> :
                       item.status === 'failed' ? <XCircle className="h-3 w-3" /> :
                       <Clock className="h-3 w-3" />}
                      {statusInfo.label}
                    </span>
                  </div>
                  {expandedId === String(item.id) && (
                    <div className="mt-3 pt-3 border-t text-xs space-y-2">
                      <p className="text-muted-foreground">备注: {item.remark || '无'}</p>
                      <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); setShowTaskForm(true) }}>
                        指派整改任务
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <InspectionTaskModal
        open={showTaskForm}
        onClose={() => setShowTaskForm(false)}
        onSubmit={handleCreateTask}
      />

      {taskResult && (
        <p className="text-xs text-green-600">整改任务已创建</p>
      )}
    </div>
  )
}
