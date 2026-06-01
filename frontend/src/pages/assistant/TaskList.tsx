import { useState, useEffect } from 'react'
import { fetchAssistantTasks, type AssistantTask } from '@/api/assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { Calendar, Check } from 'lucide-react'

export default function TaskList() {
  const [tasks, setTasks] = useState<AssistantTask[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchAssistantTasks().then((data) => {
      if (cancelled) return
      setTasks(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-16 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">任务列表</h2>
      {tasks.map((task) => (
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
    </div>
  )
}
