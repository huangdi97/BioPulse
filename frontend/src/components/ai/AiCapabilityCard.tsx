import { Card } from '@/components/ui/card'

interface AiCapabilityCardProps {
  icon: React.ReactNode
  title: string
  description: string
  status: 'online' | 'offline' | 'simulated'
}

const statusColors = {
  online: { dot: 'bg-green-500', label: '在线', bg: 'bg-green-50' },
  offline: { dot: 'bg-red-500', label: '离线', bg: 'bg-red-50' },
  simulated: { dot: 'bg-yellow-500', label: '模拟', bg: 'bg-yellow-50' },
}

export default function AiCapabilityCard({ icon, title, description, status }: AiCapabilityCardProps) {
  const sc = statusColors[status]

  return (
    <Card className="p-4 flex items-start gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold">{title}</h4>
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${sc.bg}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${sc.dot}`} />
            {sc.label}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </Card>
  )
}
