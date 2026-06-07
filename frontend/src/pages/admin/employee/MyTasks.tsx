import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  priorityColors,
  priorityLabels,
  statusLabels,
} from '@/mock/adminEmployee'
import { fetchEmployeeTasks } from '@/api/adminEmployee'
import type { TaskItem } from '@/api/adminEmployee'

export default function MyTasks() {
  const [tasks, setTasks] = useState<TaskItem[]>([])

  useEffect(() => {
    fetchEmployeeTasks().then(setTasks)
  }, [])

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">任务列表</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{task.title}</p>
                <p className="text-xs text-muted-foreground">截止: {task.dueDate}</p>
              </div>
              <Badge className={`text-xs ${priorityColors[task.priority]}`}>
                {priorityLabels[task.priority]}
              </Badge>
              <span className={`text-xs font-medium ${
                task.status === 'completed' ? 'text-green-600' : 'text-orange-600'
              }`}>
                {statusLabels[task.status]}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
