import { useMemo } from "react"

// TODO: 接后端API
const mockTrendData = [
  { date: "05-10", positive: 0.65, neutral: 0.22, negative: 0.13 },
  { date: "05-11", positive: 0.58, neutral: 0.28, negative: 0.14 },
  { date: "05-12", positive: 0.72, neutral: 0.18, negative: 0.10 },
  { date: "05-13", positive: 0.60, neutral: 0.25, negative: 0.15 },
  { date: "05-14", positive: 0.68, neutral: 0.20, negative: 0.12 },
  { date: "05-15", positive: 0.75, neutral: 0.15, negative: 0.10 },
  { date: "05-16", positive: 0.70, neutral: 0.20, negative: 0.10 },
]

// TODO: 接后端API
const mockSentimentDistribution = {
  positive: 0.68,
  neutral: 0.20,
  negative: 0.12,
}

// TODO: 接后端API
const mockCompetitorVolume = [
  { name: "本产品", volume: 4200 },
  { name: "竞品A", volume: 3800 },
  { name: "竞品B", volume: 3100 },
  { name: "竞品C", volume: 2500 },
  { name: "竞品D", volume: 1800 },
]

const LINE_COLORS = {
  positive: "var(--clr-success, #22c55e)",
  neutral: "var(--clr-warning, #eab308)",
  negative: "var(--clr-error, #ef4444)",
}

const MAX_TREND = 1.0
const TREND_CHART_HEIGHT = 200

export default function SentimentDashboard() {
  // TODO: 接后端API - 替换mock数据
  const trend = useMemo(() => mockTrendData, [])
  const distribution = useMemo(() => mockSentimentDistribution, [])
  const volume = useMemo(() => mockCompetitorVolume, [])

  const maxVolume = Math.max(...volume.map((v) => v.volume))

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: "var(--clr-text-primary)" }}>
          竞品舆情看板
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>
          情感趋势、情感分布与竞品声量对比
        </p>
      </div>

      {/* 情感趋势折线图 */}
      <div
        className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5"
      >
        <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>
          情感趋势
        </h3>
        {/* TODO: 接后端API - 趋势数据 */}
        <div className="relative" style={{ height: TREND_CHART_HEIGHT }}>
          {/* Y轴刻度 */}
          <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-xs" style={{ color: "var(--clr-text-secondary)" }}>
            <span>100%</span>
            <span>75%</span>
            <span>50%</span>
            <span>25%</span>
            <span>0%</span>
          </div>

          {/* 图表区域 */}
          <div className="relative ml-10 mr-2" style={{ height: "100%" }}>
            {/* 网格线 */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
              <div
                key={ratio}
                className="absolute left-0 right-0 border-t"
                style={{ top: `${ratio * 100}%`, borderColor: "var(--clr-gray-20, #e5e7eb)" }}
              />
            ))}

            {/* 线条和点位 */}
            {(["positive", "neutral", "negative"] as const).map((key) => (
              <div key={key} className="absolute inset-0">
                {trend.map((point, i) => {
                  const x = `${(i / (trend.length - 1)) * 100}%`
                  const y = `${(1 - point[key] / MAX_TREND) * 100}%`
                  return (
                    <div
                      key={point.date}
                      className="absolute"
                      style={{ left: x, top: y, transform: "translate(-50%, -50%)", zIndex: 10 }}
                    >
                      <div
                        className="rounded-full"
                        style={{
                          width: 8,
                          height: 8,
                          backgroundColor: LINE_COLORS[key],
                          border: "2px solid var(--clr-surface-card)",
                        }}
                      />
                    </div>
                  )
                })}
              </div>
            ))}

            {/* X轴日期 */}
            <div
              className="absolute left-0 right-0 flex justify-between text-xs"
              style={{ bottom: -20, color: "var(--clr-text-secondary)" }}
            >
              {trend.map((point) => (
                <span key={point.date}>{point.date}</span>
              ))}
            </div>
          </div>
        </div>

        {/* 图例 */}
        <div className="flex justify-center gap-5 mt-6">
          {(["positive", "neutral", "negative"] as const).map((key) => (
            <div key={key} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--clr-text-secondary)" }}>
              <span className="w-3 h-0.5 rounded" style={{ backgroundColor: LINE_COLORS[key] }} />
              {key === "positive" ? "正面" : key === "neutral" ? "中性" : "负面"}
            </div>
          ))}
        </div>
      </div>

      {/* 情感分布 + 竞品声量对比 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 情感分布 */}
        <div
          className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5"
        >
          <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>
            情感分布
          </h3>
          {/* TODO: 接后端API - 分布数据 */}
          <div className="space-y-4">
            {(["positive", "neutral", "negative"] as const).map((key) => {
              const pct = Math.round(distribution[key] * 100)
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span style={{ color: "var(--clr-text-primary)" }}>
                      {key === "positive" ? "正面" : key === "neutral" ? "中性" : "负面"}
                    </span>
                    <span style={{ color: "var(--clr-text-secondary)" }}>{pct}%</span>
                  </div>
                  <div
                    className="w-full h-3 rounded-full overflow-hidden"
                    style={{ backgroundColor: "var(--clr-gray-10, #f3f4f6)" }}
                  >
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: LINE_COLORS[key],
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 竞品声量对比 */}
        <div
          className="rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] p-5"
        >
          <h3 className="text-base font-semibold mb-4" style={{ color: "var(--clr-text-primary)" }}>
            竞品声量对比
          </h3>
          {/* TODO: 接后端API - 声量数据 */}
          <div className="space-y-3">
            {volume.map((item) => {
              const barWidth = (item.volume / maxVolume) * 100
              return (
                <div key={item.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span style={{ color: "var(--clr-text-primary)" }}>{item.name}</span>
                    <span style={{ color: "var(--clr-text-secondary)" }}>
                      {item.volume.toLocaleString()}
                    </span>
                  </div>
                  <div
                    className="w-full h-4 rounded overflow-hidden"
                    style={{ backgroundColor: "var(--clr-gray-10, #f3f4f6)" }}
                  >
                    <div
                      className="h-full rounded transition-all"
                      style={{
                        width: `${barWidth}%`,
                        backgroundColor:
                          item.name === "本产品"
                            ? "var(--clr-brand, #3b82f6)"
                            : "var(--clr-gray-30, #d1d5db)",
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
