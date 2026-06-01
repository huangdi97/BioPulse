import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface TaskItem {
  id: number
  title: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'completed'
}

const mockTasks: TaskItem[] = [
  { id: 1, title: '拜访华东医院张主任', dueDate: '2026-06-05', priority: 'high', status: 'pending' },
  { id: 2, title: '提交5月拜访报告', dueDate: '2026-06-02', priority: 'high', status: 'completed' },
  { id: 3, title: '合规培训课程学习', dueDate: '2026-06-10', priority: 'medium', status: 'pending' },
  { id: 4, title: '更新客户信息表', dueDate: '2026-06-07', priority: 'low', status: 'pending' },
  { id: 5, title: '准备产品演示材料', dueDate: '2026-06-03', priority: 'medium', status: 'completed' },
  { id: 6, title: '参加区域销售会议', dueDate: '2026-06-08', priority: 'high', status: 'pending' },
]

const priorityColors: Record<string, string> = {
  high: 'bg-red-50 text-red-700 border-red-200',
  medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  low: 'bg-blue-50 text-blue-700 border-blue-200',
}

const priorityLabels: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

const statusLabels: Record<string, string> = {
  pending: '待处理',
  completed: '已完成',
}

export default function MyTasks() {
  const [tasks] = useState(mockTasks)

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
