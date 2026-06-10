import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle, XCircle, Clock, Plus } from 'lucide-react'
import client, { getApiUrl } from '@/api/client'

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  passed: { label: '已通过', color: 'text-green-600 bg-green-50' },
  failed: { label: '未通过', color: 'text-red-600 bg-red-50' },
  pending: { label: '待检查', color: 'text-yellow-600 bg-yellow-50' },
}

const CATEGORIES = ['全部', '资质证照', '人员培训', '冷链管理', '样品管理']

export default function InspectionChecklist() {
  const [checklist, setChecklist] = useState<any[]>([])
  const [category, setCategory] = useState('全部')
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskForm, setTaskForm] = useState({ title: '', description: '', assignee: '', deadline: '' })
  const [taskResult, setTaskResult] = useState<any>(null)

  function loadChecklist() {
    setLoading(true)
    const params = category === '全部' ? '' : `?category=${category}`
    client.get(getApiUrl('cloud', `/api/inspection/checklist${params}`)).then(res => {
      setChecklist((res as any[]) || [])
    }).finally(() => setLoading(false))
  }

  useEffect(() => { loadChecklist() }, [category])

  async function handleCreateTask() {
    const res = await client.post(getApiUrl('cloud', '/api/inspection/task'), taskForm)
    setTaskResult(res)
    setShowTaskForm(false)
    setTaskForm({ title: '', description: '', assignee: '', deadline: '' })
  }

  return (
    <div className="space-y-4">
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
          {checklist.map((item: any) => {
            const statusInfo = STATUS_MAP[item.status] || { label: item.status, color: 'text-gray-600 bg-gray-50' }
            return (
              <Card key={item.id} className="cursor-pointer" onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}>
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
                  {expandedId === item.id && (
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

      {showTaskForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowTaskForm(false)}>
          <Card className="w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
            <CardHeader>
              <CardTitle className="text-base">创建整改任务</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs">任务标题</Label>
                <Input value={taskForm.title} onChange={e => setTaskForm(f => ({ ...f, title: e.target.value }))} placeholder="输入标题" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">描述</Label>
                <Input value={taskForm.description} onChange={e => setTaskForm(f => ({ ...f, description: e.target.value }))} placeholder="可选" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">负责人</Label>
                <Input value={taskForm.assignee} onChange={e => setTaskForm(f => ({ ...f, assignee: e.target.value }))} placeholder="输入姓名" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">截止日期</Label>
                <Input type="date" value={taskForm.deadline} onChange={e => setTaskForm(f => ({ ...f, deadline: e.target.value }))} />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowTaskForm(false)}>取消</Button>
                <Button onClick={handleCreateTask}>创建</Button>
              </div>
              {taskResult && (
                <p className="text-xs text-green-600">整改任务已创建: {taskResult.id}</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
