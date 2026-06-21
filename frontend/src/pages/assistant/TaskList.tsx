import { useState, useEffect, useMemo } from 'react'
import { fetchAssistantTasks, type AssistantTask } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import AgentInsightBar from '@/components/AgentInsightBar'
import { Calendar, Check } from 'lucide-react'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const STATUS_OPTIONS = [
  { value: '全部', label: '全部状态' },
  { value: 'pending', label: '待办' },
  { value: 'completed', label: '已完成' },
]

const TYPE_OPTIONS = [
  { value: '全部', label: '全部类型' },
  { value: 'high', label: '高优先级' },
  { value: 'medium', label: '中优先级' },
]

export default function TaskList() {
  const [tasks, setTasks] = useState<AssistantTask[]>([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('全部')
  const [type, setType] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchAssistantTasks().then((data) => {
      if (cancelled) return
      setTasks(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return tasks.filter((t) => {
      const matchStatus = status === '全部' || t.status === status
      const matchType = type === '全部' || t.priority === type
      return matchStatus && matchType
    })
  }, [tasks, status, type])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-16 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="assistant_tasks" />
      <h2 className="text-lg font-semibold">任务列表</h2>
      <div className="flex gap-2 flex-wrap">
        <FilterDropdown label="状态" value={status} options={STATUS_OPTIONS} onChange={setStatus} />
        <FilterDropdown label="类型" value={type} options={TYPE_OPTIONS} onChange={setType} />
      </div>
      {filtered.map((task) => (
        <Card key={task.id} className={task.status === 'completed' ? 'opacity-60' : ''}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 mt-0.5 ${task.status === 'completed' ? 'bg-green-100 border-green-400' : 'border-muted-foreground/30'}`}>
                {task.status === 'completed' && <Check className="h-3 w-3 text-green-600" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{task.title}</p>
                {task.description && <p className="text-xs text-muted-foreground mt-0.5">{task.description}</p>}
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" /><span>{task.dueDate}</span>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${task.priority === 'high' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>{task.priority === 'high' ? '高优' : '中优'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的任务</div>
      )}
    </div>
  )
}
