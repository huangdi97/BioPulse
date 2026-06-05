import { useState, useMemo, type ReactNode } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card"
import { cn } from "../../lib/utils"
import { scenarios, trainingRecords, abilityAssessment } from "../../api/mockCoach"
import ScenarioCard from "../../components/coach/ScenarioCard"
import TrainingRecordTable from "../../components/coach/TrainingRecordTable"
import AbilityRadar from "../../components/coach/AbilityRadar"

const tabs = ['场景库', '训练记录', '能力评估'] as const
type Tab = typeof tabs[number]

function TabList({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <div className="flex gap-1 p-1 rounded-[var(--radius-lg)]" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
      {tabs.map(t => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={cn(
            'flex-1 px-4 py-2 text-sm font-medium rounded-[var(--radius-md)] transition-colors',
            active === t
              ? 'bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] text-[var(--clr-text-primary)]'
              : 'text-[var(--clr-text-secondary)] hover:text-[var(--clr-text-primary)]'
          )}
        >
          {t}
        </button>
      ))}
    </div>
  )
}

function KpiCard({ title, value, accent }: { title: string; value: string; accent: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold" style={{ color: accent }}>{value}</p>
      </CardContent>
    </Card>
  )
}

export default function TrainingPage() {
  const [activeTab, setActiveTab] = useState<Tab>('场景库')

  const totalTrainings = trainingRecords.length
  const avgScore = Math.round(trainingRecords.reduce((s, r) => s + r.score, 0) / trainingRecords.length)
  const pendingCount = scenarios.filter(s => !s.completed).length

  const tabContent: Record<Tab, ReactNode> = useMemo(() => ({
    '场景库': (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map(s => <ScenarioCard key={s.id} scenario={s} />)}
      </div>
    ),
    '训练记录': <TrainingRecordTable records={trainingRecords} />,
    '能力评估': <AbilityRadar data={abilityAssessment} />,
  }), [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--clr-text-primary)' }}>销售教练</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--clr-text-secondary)' }}>情景模拟训练与能力评估</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="总训练次数" value={String(totalTrainings)} accent="var(--clr-brand)" />
        <KpiCard title="平均分" value={`${avgScore}`} accent="var(--clr-mode-pass)" />
        <KpiCard title="待练习场景" value={String(pendingCount)} accent="var(--clr-mode-warn)" />
      </div>

      <TabList active={activeTab} onChange={setActiveTab} />

      {tabContent[activeTab]}
    </div>
  )
}
