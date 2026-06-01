import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchDashboardSummary } from '@/api/dashboard'
import { fetchTasks, completeTask } from '@/api/tasks'
import { fetchSuggestions } from '@/api/recommends'
import type { DashboardSummary, Task, AiSuggestion } from '@/types'
import StatCard from '@/components/StatCard'
import AiSuggestionCard from '@/components/AiSuggestionCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ClipboardList, CalendarCheck, AlertTriangle, Check } from 'lucide-react'

export default function RepDashboard() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<DashboardSummary>({
    pendingTasks: 0,
    todayVisits: 0,
    complianceAlerts: 0,
  })
  const [tasks, setTasks] = useState<Task[]>([])
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchDashboardSummary(), fetchTasks(), fetchSuggestions()]).then(
      ([summaryData, tasksData, suggestionsData]) => {
        if (cancelled) return
        setSummary(summaryData)
        setTasks(tasksData)
        setSuggestions(suggestionsData)
        setLoading(false)
      }
    )
    return () => {
      cancelled = true
    }
  }, [])

  const handleToggleTask = async (id: number) => {
    const task = tasks.find((t) => t.id === id)
    if (!task || task.status === 'completed') return
    await completeTask(id)
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: 'completed' as const } : t))
    )
    setSummary((prev) => ({
      ...prev,
      pendingTasks: Math.max(0, prev.pendingTasks - 1),
    }))
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="flex gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex-1 h-24 bg-muted rounded-xl" />
          ))}
        </div>
        <div className="h-48 bg-muted rounded-xl" />
        <div className="h-32 bg-muted rounded-xl" />
      </div>
    )
  }

  const pendingTasks = tasks.filter((t) => t.status === 'pending')

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <StatCard
          icon={<ClipboardList className="h-5 w-5 text-blue-600" />}
          label="待办任务"
          value={summary.pendingTasks}
          trend="up"
          trendValue="较昨日+1"
          onClick={() => navigate('/rep/tasks')}
        />
        <StatCard
          icon={<CalendarCheck className="h-5 w-5 text-green-600" />}
          label="今日计划拜访"
          value={summary.todayVisits}
          onClick={() => navigate('/rep/visits')}
        />
        <StatCard
          icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
          label="合规提醒"
          value={summary.complianceAlerts}
          trend="down"
          trendValue="较上周-2"
          onClick={() => navigate('/rep/tasks')}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">待办任务</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {pendingTasks.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              暂无待办任务
            </p>
          ) : (
            pendingTasks.map((task) => (
              <button
                key={task.id}
                onClick={() => handleToggleTask(task.id)}
                className="w-full flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors text-left"
              >
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-muted-foreground/30">
                  <Check className="h-3 w-3 text-transparent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{task.title}</p>
                  {task.description && (
                    <p className="text-xs text-muted-foreground truncate">
                      {task.description}
                    </p>
                  )}
                </div>
                {task.dueDate && (
                  <span className="text-xs text-muted-foreground shrink-0">
                    {task.dueDate}
                  </span>
                )}
              </button>
            ))
          )}
        </CardContent>
      </Card>

      <AiSuggestionCard suggestions={suggestions} maxItems={1} />
    </div>
  )
}
