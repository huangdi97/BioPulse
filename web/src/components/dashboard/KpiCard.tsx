import type { KpiCard as KpiCardType } from "../../types/dashboard"
import * as Icons from "lucide-react"

interface Props {
  data: KpiCardType
  accentColor?: string
}

export default function KpiCard({ data, accentColor = "var(--clr-brand-light)" }: Props) {
  const Icon = (Icons as any)[data.icon] || Icons.HelpCircle
  const arrow = data.trend === "up" ? "▲" : data.trend === "down" ? "▼" : "―"
  const color = data.trend === "up" ? "var(--clr-success)" : data.trend === "down" ? "var(--clr-error)" : "var(--clr-text-secondary)"

  return (
    <div className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5 flex items-center gap-4 cursor-pointer hover:shadow-[var(--shadow-raised)] transition-shadow">
      <div
        className="w-11 h-11 rounded-[var(--radius-md)] flex items-center justify-center shrink-0"
        style={{ backgroundColor: accentColor }}
      >
        <Icon className="w-5 h-5" color="var(--clr-brand)" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm" style={{ color: "var(--clr-text-secondary)" }}>{data.title}</p>
        <p className="text-[32px] font-semibold leading-tight" style={{ color: "var(--clr-text-primary)" }}>
          {data.value}
        </p>
      </div>
      <div className="text-sm font-medium shrink-0" style={{ color }}>
        <span>{arrow}</span>
        <span className="ml-0.5">{data.change > 0 ? "+" : ""}{data.change}%</span>
      </div>
    </div>
  )
}
