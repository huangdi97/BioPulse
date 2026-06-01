import { useState, useEffect, useCallback } from 'react'
import { fetchTasks, completeTask } from '@/api/tasks'
import type { Task } from '@/types'
import { Check, CheckCircle2, X } from 'lucide-react'

type TabKey = 'all' | 'pending' | 'completed'

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabKey>('pending')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  const loadTasks = useCallback(() => {
    setLoading(true)
    fetchTasks().then((data) => {
      setTasks(data)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  const handleComplete = async (id: number) => {
    const task = tasks.find((t) => t.id === id)
    if (!task || task.status === 'completed') return
    await completeTask(id)
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: 'completed' as const, completedDate: new Date().toISOString().slice(0, 10) } : t))
    )
    setSelectedTask(null)
  }

  const filteredTasks = tasks.filter((t) => {
    if (activeTab === 'all') return true
    return t.status === activeTab
  })

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: 'all', label: '全部', count: tasks.length },
    { key: 'pending', label: '待办', count: tasks.filter((t) => t.status === 'pending').length },
    { key: 'completed', label: '已完成', count: tasks.filter((t) => t.status === 'completed').length },
  ]

  return (
    <div className="space-y-4">
      <div className="flex rounded-lg bg-muted p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
            <span className="ml-1 text-xs opacity-60">{tab.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-muted rounded-lg" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <p className="text-sm">
            {activeTab === 'pending'
              ? '暂无待办任务'
              : activeTab === 'completed'
                ? '暂无已完成任务'
                : '暂无任务'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              onClick={() => setSelectedTask(task)}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-muted/50 ${
                task.status === 'completed' ? 'bg-muted/30' : 'bg-card'
              }`}
            >
              {task.status === 'pending' ? (
                <button
                  onClick={(e) => { e.stopPropagation(); handleComplete(task.id) }}
                  className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-muted-foreground/30 hover:border-green-500 hover:bg-green-50 transition-colors"
                >
                  <Check className="h-3 w-3 text-transparent" />
                </button>
              ) : (
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-green-500">
                  <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm truncate ${
                    task.status === 'completed'
                      ? 'line-through text-muted-foreground'
                      : 'font-medium'
                  }`}
                >
                  {task.title}
                </p>
                {task.description && (
                  <p className="text-xs text-muted-foreground truncate">
                    {task.description}
                  </p>
                )}
              </div>
              <span className="text-xs text-muted-foreground shrink-0">
                {task.dueDate}
              </span>
            </div>
          ))}
        </div>
      )}

      {selectedTask && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setSelectedTask(null)}
        >
          <div
            className="bg-background rounded-lg shadow-lg max-w-sm w-full mx-4 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">任务详情</h3>
              <button
                onClick={() => setSelectedTask(null)}
                className="p-1 rounded-md hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium">{selectedTask.title}</p>
              </div>
              {selectedTask.description && (
                <div>
                  <p className="text-xs text-muted-foreground">描述</p>
                  <p className="text-sm">{selectedTask.description}</p>
                </div>
              )}
              {selectedTask.dueDate && (
                <div>
                  <p className="text-xs text-muted-foreground">截止日期</p>
                  <p className="text-sm">{selectedTask.dueDate}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-muted-foreground">状态</p>
                <span
                  className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                    selectedTask.status === 'pending'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-green-100 text-green-700'
                  }`}
                >
                  {selectedTask.status === 'pending' ? '待办' : '已完成'}
                </span>
              </div>
            </div>
            <div className="mt-6 flex gap-2 justify-end">
              {selectedTask.status === 'pending' && (
                <button
                  onClick={() => handleComplete(selectedTask.id)}
                  className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  标记完成
                </button>
              )}
              <button
                onClick={() => setSelectedTask(null)}
                className="px-4 py-2 rounded-md border text-sm font-medium hover:bg-muted transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
