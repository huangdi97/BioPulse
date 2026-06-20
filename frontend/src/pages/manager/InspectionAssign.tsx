import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Users } from 'lucide-react'
import { fetchDashboard, createTask } from '@/api/inspection'
import InspectionTaskModal from '@/components/InspectionTaskModal'
import type { InspectionTask, TaskFormData } from '@/types/inspection'

const DEFAULT_REPS = ['张代表', '李代表', '王代表', '赵代表', '刘代表']

export default function InspectionAssign() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<InspectionTask[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [result, setResult] = useState<unknown>(null)

  useEffect(() => {
    let cancelled = false
    fetchDashboard().then(data => {
      if (!cancelled) setTasks(Array.isArray(data.history_records) ? data.history_records as unknown as InspectionTask[] : [])
    }).finally(() => setLoading(false))
    return () => { cancelled = true }
  }, [])

  async function handleCreate(data: TaskFormData) {
    const res = await createTask(data)
    setResult(res)
    setShowForm(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/manager/inspection')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> 返回
        </Button>
        <div>
          <h2 className="text-lg font-semibold">整改任务分派</h2>
          <p className="text-sm text-muted-foreground">选择代表、填写整改要求、设定截止日期</p>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={() => setShowForm(true)}>
          <Users className="h-4 w-4 mr-1" /> 新建整改任务
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground py-8 text-center">加载中...</p>
      ) : tasks.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center">暂无整改任务</p>
      ) : (
        <div className="space-y-2">
          {tasks.map((t: InspectionTask, i: number) => (
            <Card key={t.id || i}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{t.event || t.title || `整改任务 ${i + 1}`}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>负责人: {t.owner || t.assignee || '-'}</span>
                    <span>日期: {t.date || t.deadline || '-'}</span>
                    <span>阶段: {t.capa_stage || '-'}</span>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  (t.score || 0) >= 80 ? 'text-green-600 bg-green-50' : (t.score || 0) >= 60 ? 'text-yellow-600 bg-yellow-50' : 'text-red-600 bg-red-50'
                }`}>
                  评分: {t.score ?? '-'}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <InspectionTaskModal
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
        title="分派整改任务"
        defaultReps={DEFAULT_REPS}
      />

      {result && (
        <p className="text-xs text-green-600">整改任务已创建</p>
      )}
    </div>
  )
}
