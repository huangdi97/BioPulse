import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import type { VisitStat } from "../../types/dashboard"

interface Props {
  data: VisitStat[]
}

export default function TrendChart({ data }: Props) {
  return (
    <div
      className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5"
    >
      <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>
        拜访趋势
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-gray-20)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "var(--clr-text-secondary)" }}
            tickFormatter={(v: string) => v.slice(5)}
            stroke="var(--clr-gray-30)"
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 11, fill: "var(--clr-text-secondary)" }}
            stroke="var(--clr-gray-30)"
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11, fill: "var(--clr-text-secondary)" }}
            stroke="var(--clr-gray-30)"
            domain={[85, 100]}
          />
          <Tooltip
            contentStyle={{
              background: "var(--clr-white)",
              border: "1px solid var(--clr-gray-20)",
              borderRadius: 6,
              fontSize: 12,
            }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="count"
            stroke="var(--clr-brand)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--clr-brand)" }}
            activeDot={{ r: 5 }}
            name="拜访数"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="passRate"
            stroke="var(--clr-success)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--clr-success)" }}
            activeDot={{ r: 5 }}
            name="合规率"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
