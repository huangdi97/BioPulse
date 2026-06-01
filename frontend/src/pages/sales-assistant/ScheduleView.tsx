import { useState, useEffect } from 'react'
import { fetchSchedule, type ScheduleItem } from '@/api/sales-assistant-api'
import { Card, CardContent } from '@/components/ui/card'
import { Clock, MapPin, User } from 'lucide-react'

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  scheduled: { label: '已安排', color: 'bg-blue-50 text-blue-700' },
  preparing: { label: '准备中', color: 'bg-yellow-50 text-yellow-700' },
  completed: { label: '已完成', color: 'bg-green-50 text-green-700' },
}

export default function ScheduleView() {
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchSchedule().then((data) => {
      if (cancelled) return
      setSchedule(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="space-y-3">{[1, 2, 3].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-16 bg-muted rounded" /></CardContent></Card>)}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">日程安排</h2>
      {schedule.map((item) => {
        const status = STATUS_MAP[item.status] ?? STATUS_MAP.scheduled
        return (
          <Card key={item.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <p className="text-sm font-semibold">{item.title}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" /><span>{item.time}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3" /><span>{item.location}</span>
                  </div>
                  {item.relatedHcp !== '-' && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" /><span>{item.relatedHcp}</span>
                    </div>
                  )}
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                  {status.label}
                </span>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
