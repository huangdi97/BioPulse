import { useState, useEffect, useRef } from "react"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { useNavigate } from "react-router-dom"
import KpiCard from "../../components/dashboard/KpiCard"
import TrendChart from "../../components/dashboard/TrendChart"
import DataTable from "../../components/dashboard/DataTable"
import { Badge } from "../../components/ui/Badge"
import { getPharmaKpis, getVisitTrends, getTeamRanks, getViolations, getComplianceKpis } from "../../api/client"
const dateTabs = ["今日", "本周", "本月"]

const severityVariant: Record<string, "error" | "warning" | "neutral"> = {
  high: "error",
  medium: "warning",
  low: "neutral",
}

export default function PharmaPage() {
  const [tab, setTab] = useState(2)
  const [pharmaKpis, setPharmaKpis] = useState<any[]>([])
  const [visitTrends, setVisitTrends] = useState<any[]>([])
  const [teamRanks, setTeamRanks] = useState<any[]>([])
  const [violations, setViolations] = useState<any[]>([])
  const [compliancePieData, setCompliancePieData] = useState<{name: string; value: number; color: string}[]>([])
  const [complianceLoaded, setComplianceLoaded] = useState(false)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState<string | null>(null)
  const loadCount = useRef(0)
  const CALL_TOTAL = 5
  const onLoad = () => {
    loadCount.current += 1
    if (loadCount.current >= CALL_TOTAL) setLoading(false)
  }
  const navigate = useNavigate()

  useEffect(() => {
    getPharmaKpis().then(data => { setPharmaKpis(data); onLoad() }).catch(err => { console.error('Failed to load pharma KPIs:', err); setApiError('数据加载失败，请刷新重试'); onLoad() })
    getVisitTrends().then(data => { setVisitTrends(data); onLoad() }).catch(err => { console.error('Failed to load visit trends:', err); setApiError('数据加载失败，请刷新重试'); onLoad() })
    getTeamRanks().then(data => { setTeamRanks(data); onLoad() }).catch(err => { console.error('Failed to load team ranks:', err); setApiError('数据加载失败，请刷新重试'); onLoad() })
    getViolations().then(data => { setViolations(data); onLoad() }).catch(err => { console.error('Failed to load violations:', err); setApiError('数据加载失败，请刷新重试'); onLoad() })
    getComplianceKpis()
      .then(kpis => {
        const findRate = (keywords: string[]) => {
          const card = kpis.find(k => keywords.some(kw => k.title.includes(kw)))
          return card ? Number(card.value) : 0
        }
        const passRate = findRate(["通过", "合规"])
        const warnRate = findRate(["警告"])
        const violRate = findRate(["违规"])
        const hasData = passRate > 0 || warnRate > 0 || violRate > 0
        if (hasData) {
          setCompliancePieData([
            { name: "通过", value: passRate, color: "var(--clr-success)" },
            { name: "警告", value: warnRate, color: "var(--clr-warning)" },
            { name: "违规", value: violRate, color: "var(--clr-error)" },
          ])
        }
        setComplianceLoaded(true)
        onLoad()
      })
      .catch(err => {
        console.error('Failed to load compliance KPIs:', err)
        setApiError('数据加载失败，请刷新重试')
        setComplianceLoaded(true)
        onLoad()
      })
  }, [])

  const rankColumns = [
    { header: "代表", accessorKey: "name" },
    { header: "拜访数", accessorKey: "visits" },
    { header: "合规率", accessorKey: "complianceRate", cell: (v: unknown) => `${v}%` },
    { header: "成单数", accessorKey: "deals" },
  ]

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <span className="text-sm" style={{ color: "var(--clr-text-secondary)" }}>加载中...</span>
    </div>
  )

  return (
    <div className="space-y-5">
      {apiError && (
        <div className="rounded-lg px-4 py-3 text-sm font-medium" style={{ backgroundColor: "#fef2f2", color: "var(--clr-error)", border: "1px solid var(--clr-error)" }}>
          数据加载失败，请刷新重试
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: "var(--clr-text-primary)" }}>医药看板</h1>
          <p className="text-sm mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>医药代表运营全景</p>
        </div>
        <div className="flex gap-1 rounded-lg p-0.5" style={{ backgroundColor: "var(--clr-gray-10)" }}>
          {dateTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setTab(i)}
              className="px-4 py-1.5 text-sm font-medium rounded-md transition-colors"
              style={{
                color: i === tab ? "var(--clr-text-primary)" : "var(--clr-text-secondary)",
                backgroundColor: i === tab ? "var(--clr-white)" : "transparent",
                boxShadow: i === tab ? "var(--shadow-border)" : "none",
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {pharmaKpis.map((kpi) => (
          <KpiCard key={kpi.title} data={kpi} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <TrendChart data={visitTrends} />
        </div>
        <div className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5">
          <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>合规率</h3>
          {!complianceLoaded ? (
            <div className="flex items-center justify-center h-[280px] text-sm" style={{ color: "var(--clr-text-secondary)" }}>加载中...</div>
          ) : compliancePieData.length === 0 ? (
            <div className="flex items-center justify-center h-[280px] text-sm" style={{ color: "var(--clr-text-secondary)" }}>暂无合规数据</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={compliancePieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {compliancePieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <text x="50%" y="48%" textAnchor="middle" dominantBaseline="middle" fontSize={28} fontWeight={700} fill="var(--clr-text-primary)">
                    {(compliancePieData.find(d => d.name === "通过")?.value ?? 0).toFixed(1)}%
                  </text>
                  <text x="50%" y="58%" textAnchor="middle" dominantBaseline="middle" fontSize={11} fill="var(--clr-text-secondary)">
                    总合规率
                  </text>
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-2">
                {compliancePieData.map((item) => (
                  <div key={item.name} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--clr-text-secondary)" }}>
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
                    {item.name}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <DataTable
            columns={rankColumns}
            data={teamRanks as unknown as Record<string, unknown>[]}
          />
        </div>
        <div className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold" style={{ color: "var(--clr-text-primary)" }}>最近违规</h3>
            <button
              onClick={() => navigate("/compliance/overview")}
              className="text-sm font-medium hover:underline"
              style={{ color: "var(--clr-brand)" }}
            >
              查看全部
            </button>
          </div>
          <div className="space-y-3">
            {violations.slice(0, 3).map((v) => (
              <div key={v.id} className="flex items-center justify-between py-2 border-b last:border-0" style={{ borderColor: "var(--clr-gray-20)" }}>
                <div className="min-w-0 flex-1">
                  <p className="text-sm truncate" style={{ color: "var(--clr-text-primary)" }}>{v.detail}</p>
                  <p className="text-xs mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>{v.repName} · {v.date}</p>
                </div>
                <Badge variant={severityVariant[v.severity]}>{v.severity === "high" ? "高" : v.severity === "medium" ? "中" : "低"}</Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
