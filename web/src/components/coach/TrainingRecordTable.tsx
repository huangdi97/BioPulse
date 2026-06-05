import { useState, useMemo } from "react"
import { Badge } from "../ui/Badge"
import { cn } from "../../lib/utils"
import type { TrainingRecord } from "../../types/coach"

interface Props {
  records: TrainingRecord[]
}

const filters = ['全部', '近期', '按场景'] as const
type Filter = typeof filters[number]

function scoreBadge(score: number): 'success' | 'warning' | 'error' {
  if (score > 90) return 'success'
  if (score > 70) return 'warning'
  return 'error'
}

export default function TrainingRecordTable({ records }: Props) {
  const [activeFilter, setActiveFilter] = useState<Filter>('全部')

  const filtered = useMemo(() => {
    const sorted = [...records].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    if (activeFilter === '近期') {
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      return sorted.filter(r => new Date(r.date) >= weekAgo)
    }
    if (activeFilter === '按场景') {
      const groups = new Map<string, TrainingRecord[]>()
      for (const r of sorted) {
        const list = groups.get(r.scenario_name) || []
        list.push(r)
        groups.set(r.scenario_name, list)
      }
      return Array.from(groups.values()).flatMap(g => g)
    }
    return sorted
  }, [records, activeFilter])

  const top5Ids = new Set(
    [...records].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 5).map(r => r.id)
  )

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {filters.map(f => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={cn(
              'px-3 py-1.5 rounded-[var(--radius-md)] text-sm font-medium transition-colors',
              activeFilter === f
                ? 'bg-[var(--clr-brand)] text-[var(--clr-text-inverse)]'
                : 'bg-[var(--clr-gray-10)] text-[var(--clr-text-secondary)] hover:bg-[var(--clr-surface-hover)]'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--clr-border-default)]">
        <table className="w-full text-sm" style={{ color: 'var(--clr-text-primary)' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--clr-gray-10)' }}>
              {['日期', '场景', '得分', '时长', '薄弱环节', '亮点'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-xs" style={{ color: 'var(--clr-text-secondary)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => (
              <tr
                key={r.id}
                className="border-t border-[var(--clr-border-default)] hover:bg-[var(--clr-surface-hover)] transition-colors"
                style={top5Ids.has(r.id) ? { fontWeight: 600 } : undefined}
              >
                <td className="px-4 py-3 whitespace-nowrap">{r.date}</td>
                <td className="px-4 py-3">{r.scenario_name}</td>
                <td className="px-4 py-3">
                  <Badge variant={scoreBadge(r.score)}>{r.score}</Badge>
                </td>
                <td className="px-4 py-3">{r.duration}min</td>
                <td className="px-4 py-3" style={{ color: 'var(--clr-text-secondary)' }}>{r.weakness}</td>
                <td className="px-4 py-3" style={{ color: 'var(--clr-text-secondary)' }}>{r.strength}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
