import { useState, useMemo, useEffect } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import KpiCard from "../../components/dashboard/KpiCard"
import DataTable from "../../components/dashboard/DataTable"
import { Badge } from "../../components/ui/Badge"
import { Button } from "../../components/ui/Button"
import { getViolations, getComplianceKpis } from "../../api/client"

const severityOptions = ["全部", "高", "中", "低"] as const
const statusOptions = ["全部", "待处理", "已解决"] as const
const severityMap: Record<string, string> = { "高": "high", "中": "medium", "低": "low" }

const badgeVariant: Record<string, "error" | "warning" | "neutral"> = {
  high: "error",
  medium: "warning",
  low: "neutral",
}

const severityLabel: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
}

const violationTypes = ["统方", "利益输送", "备案异常", "场所异常"]

export default function CompliancePage() {
  const [sevFilter, setSevFilter] = useState("全部")
  const [statFilter, setStatFilter] = useState("全部")
  const [resolved, setResolved] = useState<Set<number>>(new Set())
  const [violations, setViolations] = useState<any[]>([])
  const [complianceKpis, setComplianceKpis] = useState<any[]>([])

  useEffect(() => {
    getViolations().then(setViolations).catch(err => console.error('Failed to load violations:', err))
    getComplianceKpis().then(setComplianceKpis).catch(err => console.error('Failed to load compliance KPIs:', err))
  }, [])

  const filtered = useMemo(() => {
    return violations.filter((v) => {
      if (sevFilter !== "全部" && v.severity !== severityMap[sevFilter]) return false
      const statusVal = statFilter === "待处理" ? "pending" : statFilter === "已解决" ? "resolved" : null
      if (statusVal) {
        const actualStatus = resolved.has(v.id) ? "resolved" : v.status
        if (actualStatus !== statusVal) return false
      }
      return true
    })
  }, [sevFilter, statFilter, resolved])

  const barData = useMemo(() => {
    return violationTypes.map((type) => {
      const items = violations.filter((v) => v.type === type)
      return {
        type,
        high: items.filter((v) => v.severity === "high").length,
        medium: items.filter((v) => v.severity === "medium").length,
        low: items.filter((v) => v.severity === "low").length,
      }
    })
  }, [])

  const handleResolve = (id: number) => {
    setResolved((prev) => new Set(prev).add(id))
  }

  const violationColumns = [
    { header: "日期", accessorKey: "date" },
    { header: "代表", accessorKey: "repName" },
    { header: "违规类型", accessorKey: "type" },
    { header: "详情", accessorKey: "detail" },
    {
      header: "严重度",
      accessorKey: "severity",
      cell: (v: unknown) => (
        <Badge variant={badgeVariant[v as string]}>{severityLabel[v as string]}</Badge>
      ),
    },
    {
      header: "状态",
      accessorKey: "id",
      cell: (id: unknown) => (
        <span style={{ color: resolved.has(id as number) ? "var(--clr-success)" : "var(--clr-warning)" }}>
          {resolved.has(id as number) ? "已解决" : "待处理"}
        </span>
      ),
    },
    {
      header: "操作",
      accessorKey: "id",
      cell: (id: unknown) => (
        resolved.has(id as number) ? (
          <span className="text-xs" style={{ color: "var(--clr-text-disabled)" }}>已处理</span>
        ) : (
          <Button variant="outline" size="sm" onClick={() => handleResolve(id as number)}>
            标记已处理
          </Button>
        )
      ),
    },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: "var(--clr-text-primary)" }}>合规全景</h1>
          <p className="text-sm mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>合规检查与违规监控</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 rounded-lg p-0.5" style={{ backgroundColor: "var(--clr-gray-10)" }}>
            {severityOptions.map((s) => (
              <button
                key={s}
                onClick={() => setSevFilter(s)}
                className="px-3 py-1 text-xs font-medium rounded-md transition-colors"
                style={{
                  color: s === sevFilter ? "var(--clr-text-primary)" : "var(--clr-text-secondary)",
                  backgroundColor: s === sevFilter ? "var(--clr-white)" : "transparent",
                  boxShadow: s === sevFilter ? "var(--shadow-border)" : "none",
                }}
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex gap-1 rounded-lg p-0.5" style={{ backgroundColor: "var(--clr-gray-10)" }}>
            {statusOptions.map((s) => (
              <button
                key={s}
                onClick={() => setStatFilter(s)}
                className="px-3 py-1 text-xs font-medium rounded-md transition-colors"
                style={{
                  color: s === statFilter ? "var(--clr-text-primary)" : "var(--clr-text-secondary)",
                  backgroundColor: s === statFilter ? "var(--clr-white)" : "transparent",
                  boxShadow: s === statFilter ? "var(--shadow-border)" : "none",
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {complianceKpis.map((kpi) => (
          <KpiCard key={kpi.title} data={kpi} />
        ))}
      </div>

      <DataTable
        columns={violationColumns}
        data={filtered as unknown as Record<string, unknown>[]}
      />

      <div className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5">
        <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>违规分类统计</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-gray-20)" />
            <XAxis dataKey="type" tick={{ fontSize: 11, fill: "var(--clr-text-secondary)" }} stroke="var(--clr-gray-30)" />
            <YAxis tick={{ fontSize: 11, fill: "var(--clr-text-secondary)" }} stroke="var(--clr-gray-30)" allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: "var(--clr-white)",
                border: "1px solid var(--clr-gray-20)",
                borderRadius: 6,
                fontSize: 12,
              }}
            />
            <Bar dataKey="high" stackId="a" fill="#da1e28" name="高严重度" radius={[0, 0, 0, 0]} />
            <Bar dataKey="medium" stackId="a" fill="#f1c21b" name="中严重度" />
            <Bar dataKey="low" stackId="a" fill="#8d8d8d" name="低严重度" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
