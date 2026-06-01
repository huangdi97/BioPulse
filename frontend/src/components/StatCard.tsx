import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface StatCardProps {
  icon: ReactNode
  label: string
  value: number
  trend?: 'up' | 'down'
  trendValue?: string
  onClick?: () => void
}

export default function StatCard({
  icon,
  label,
  value,
  trend,
  trendValue,
  onClick,
}: StatCardProps) {
  const content = (
    <CardContent className="p-4 flex items-center gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
        {trend && trendValue && (
          <div className="flex items-center gap-1 mt-1">
            {trend === 'up' ? (
              <TrendingUp className="h-3 w-3 text-green-500" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-500" />
            )}
            <span
              className={`text-xs ${
                trend === 'up' ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {trendValue}
            </span>
          </div>
        )}
      </div>
    </CardContent>
  )

  if (onClick) {
    return (
      <Card
        className="flex-1 cursor-pointer hover:shadow-md transition-shadow"
        onClick={onClick}
      >
        {content}
      </Card>
    )
  }

  return <Card className="flex-1">{content}</Card>
}
