import { useState, useEffect } from "react"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import KpiCard from "../../components/dashboard/KpiCard"
import DataTable from "../../components/dashboard/DataTable"
import { getResearchKpis, getPiSources, getProductMatchStats } from "../../api/client"
import { researchKpis as defaultResearchKpis, piSources as defaultPiSources, productMatchStats as defaultProductMatchStats } from "../../api/mockData"
import type { KpiCard as KpiCardType } from "../../types/dashboard"

const modeTabs = ["标准版", "高级版"]

const pipelineData = [
  {
    title: "报价中",
    items: [
      { name: "肿瘤药物 ALZ-101", value: "¥28万" },
      { name: "心血管 CV-202", value: "¥15万" },
      { name: "中枢神经 CN-005", value: "¥22万" },
    ],
    color: "var(--clr-brand)",
  },
  {
    title: "审批中",
    items: [
      { name: "抗感染 AI-301", value: "¥18万" },
      { name: "肿瘤药物 ONC-008", value: "¥35万" },
    ],
    color: "var(--clr-warning)",
  },
  {
    title: "已成交",
    items: [
      { name: "心血管 CV-198", value: "¥42万" },
      { name: "肿瘤药物 ALZ-099", value: "¥56万" },
    ],
    color: "var(--clr-success)",
  },
]

const matchPieColors = ["#0f62fe", "#8b5cf6", "#f59e0b", "#24a148"]

export default function ResearchPage() {
  const [mode, setMode] = useState(0)
  const [researchKpis, setResearchKpis] = useState(defaultResearchKpis)
  const [piSources, setPiSources] = useState(defaultPiSources)
  const [productMatchStats, setProductMatchStats] = useState(defaultProductMatchStats)

  useEffect(() => {
    getResearchKpis().then(setResearchKpis)
    getPiSources().then(setPiSources)
    getProductMatchStats().then(setProductMatchStats)
  }, [])

  const kpiCards: KpiCardType[] = researchKpis.map((k) => ({
    title: k.title,
    value: k.value,
    change: k.change,
    icon: k.icon,
    trend: (k.change >= 0 ? "up" : "down") as "up" | "down" | "neutral",
  }))

  const piColumns = [
    { header: "PI姓名", accessorKey: "name" },
    { header: "机构", accessorKey: "institution" },
    { header: "匹配数", accessorKey: "matches" },
    { header: "最近活跃", accessorKey: "lastActivity" },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: "var(--clr-text-primary)" }}>科研看板</h1>
          <p className="text-sm mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>PI线索与产品匹配跟踪</p>
        </div>
        <div className="flex gap-1 rounded-lg p-0.5" style={{ backgroundColor: "var(--clr-gray-10)" }}>
          {modeTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setMode(i)}
              className="px-4 py-1.5 text-sm font-medium rounded-md transition-colors"
              style={{
                color: i === mode ? "var(--clr-text-primary)" : "var(--clr-text-secondary)",
                backgroundColor: i === mode ? "var(--clr-white)" : "transparent",
                boxShadow: i === mode ? "var(--shadow-border)" : "none",
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi) => (
          <KpiCard key={kpi.title} data={kpi} accentColor="rgba(139, 92, 246, 0.1)" />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <DataTable
            columns={piColumns}
            data={piSources as unknown as Record<string, unknown>[]}
          />
        </div>
        <div className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5">
          <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>产品匹配率</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={productMatchStats}
                cx="50%" cy="50%"
                innerRadius={55}
                outerRadius={85}
                dataKey="rate"
                nameKey="category"
                strokeWidth={0}
                label={(props: any) => `${props.category} ${props.rate}%`}
                labelLine={false}
              >
                {productMatchStats.map((_, idx) => (
                  <Cell key={idx} fill={matchPieColors[idx % matchPieColors.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {pipelineData.map((col) => (
          <div
            key={col.title}
            className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5"
          >
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--clr-text-primary)" }}>
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: col.color }} />
              {col.title}
              <span className="ml-auto text-xs" style={{ color: "var(--clr-text-secondary)" }}>{col.items.length}项</span>
            </h3>
            <div className="space-y-2">
              {col.items.map((item) => (
                <div
                  key={item.name}
                  className="p-3 rounded-md text-sm"
                  style={{ backgroundColor: "var(--clr-gray-10)" }}
                >
                  <p className="font-medium" style={{ color: "var(--clr-text-primary)" }}>{item.name}</p>
                  <p className="text-xs mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
