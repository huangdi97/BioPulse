import { Card, CardContent } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { Button } from "../ui/Button"
import type { Scenario } from "../../api/mockCoach"

interface Props {
  scenario: Scenario
}

const difficultyConfig: Record<string, { variant: 'success' | 'warning' | 'error'; label: string }> = {
  '初级': { variant: 'success', label: '初级' },
  '中级': { variant: 'warning', label: '中级' },
  '高级': { variant: 'error', label: '高级' },
}

const statusConfig: Record<string, { icon: string; color: string; label: string }> = {
  completed: { icon: '✓', color: 'var(--clr-success)', label: '已完成' },
  pending: { icon: '○', color: 'var(--clr-gray-50)', label: '未开始' },
  inProgress: { icon: '⟳', color: 'var(--clr-info)', label: '进行中' },
}

export default function ScenarioCard({ scenario }: Props) {
  const dc = difficultyConfig[scenario.difficulty]
  const status = scenario.completed ? statusConfig.completed : statusConfig.pending

  return (
    <Card className="flex flex-col">
      <CardContent className="flex flex-col gap-3 flex-1">
        <div className="flex items-center justify-between">
          <h3 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--clr-text-primary)' }}>
            {scenario.name}
          </h3>
          <Badge variant={dc.variant}>{dc.label}</Badge>
        </div>

        <p style={{ fontSize: '14px', color: 'var(--clr-gray-70)' }}>
          {scenario.description}
        </p>

        <div className="flex items-center gap-1.5 text-sm" style={{ color: status.color }}>
          <span>{status.icon}</span>
          <span>{status.label}</span>
          {scenario.completed && (
            <span className="ml-auto flex items-center gap-1" style={{ color: 'var(--clr-text-primary)' }}>
              <span style={{ color: 'var(--clr-warning)' }}>★</span>
              <span className="font-medium">{scenario.score}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--clr-text-placeholder)' }}>
          <span>{scenario.category}</span>
          <span>·</span>
          <span>{scenario.duration}分钟</span>
        </div>

        <Button
          variant={scenario.completed ? 'outline' : 'default'}
          size="sm"
          className="mt-auto w-full"
        >
          {scenario.completed ? '重新训练' : '开始训练'}
        </Button>
      </CardContent>
    </Card>
  )
}
