import { useState, useEffect } from "react"
import { Card, CardContent } from "../ui/Card"
import { getTargetPipeline } from "../../api/client"

const PHASE_LABELS: Record<string, string> = {
  Phase1: "Phase 1",
  Phase2: "Phase 2",
  Phase3: "Phase 3",
  NDA: "NDA",
  Approved: "已上市",
}

const PHASE_COLORS: Record<string, string> = {
  Phase1: "#3B82F6",
  Phase2: "#F59E0B",
  Phase3: "#F97316",
  NDA: "#22C55E",
  Approved: "#10B981",
}

const PHASE_ORDER = ["Phase1", "Phase2", "Phase3", "NDA", "Approved"]

interface PipelineItem {
  id: string
  product_name: string
  company: string
  phase: string
  mechanism: string
  moa: string
  indication: string
  color_code?: string
}

interface Props {
  targetId: string | number
  targetName: string
}

export default function PipelineAssociation({ targetId, targetName }: Props) {
  const [pipeline, setPipeline] = useState<PipelineItem[]>([])
  const [loading, setLoading] = useState(true)
  const [phaseFilter, setPhaseFilter] = useState("全部")
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!expanded) return
    setLoading(true)
    getTargetPipeline(String(targetId)).then(data => {
      setPipeline(data || [])
    }).finally(() => setLoading(false))
  }, [targetId, expanded])

  const phases = ["全部", ...PHASE_ORDER]

  const filtered = phaseFilter === "全部"
    ? pipeline
    : pipeline.filter(p => p.phase === phaseFilter)

  const sorted = [...filtered].sort(
    (a, b) => PHASE_ORDER.indexOf(a.phase) - PHASE_ORDER.indexOf(b.phase)
  )

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-md transition-colors hover:bg-[var(--clr-surface-hover)]"
        style={{ color: "var(--clr-brand)" }}
      >
        <span>{expanded ? "收起" : "展开"}管线 ({pipeline.length || "..."})</span>
        <svg className={`w-3 h-3 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <Card className="mt-2">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold" style={{ color: "var(--clr-text-primary)" }}>
                {targetName} 相关在研管线
              </h4>
              <select
                value={phaseFilter}
                onChange={e => setPhaseFilter(e.target.value)}
                className="h-8 rounded-md border px-2 text-xs bg-white"
                style={{ borderColor: "var(--clr-border-default)", color: "var(--clr-text-primary)" }}
              >
                {phases.map(p => (
                  <option key={p} value={p}>
                    {p === "全部" ? "全部 Phase" : PHASE_LABELS[p] || p}
                  </option>
                ))}
              </select>
            </div>

            {loading ? (
              <p className="text-xs text-center py-4" style={{ color: "var(--clr-text-secondary)" }}>加载中...</p>
            ) : sorted.length === 0 ? (
              <p className="text-xs text-center py-4" style={{ color: "var(--clr-text-secondary)" }}>暂无管线数据</p>
            ) : (
              <div className="space-y-2">
                {sorted.map(p => (
                  <div
                    key={p.id}
                    className="flex items-center gap-3 p-2.5 rounded-lg border"
                    style={{ borderColor: "var(--clr-border-default)" }}
                  >
                    <div
                      className="w-1 h-8 rounded-full shrink-0"
                      style={{ backgroundColor: p.color_code || PHASE_COLORS[p.phase] || "#94A3B8" }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate" style={{ color: "var(--clr-text-primary)" }}>
                          {p.product_name}
                        </span>
                        <span
                          className="text-[10px] font-medium px-1.5 py-0.5 rounded-full text-white shrink-0"
                          style={{ backgroundColor: p.color_code || PHASE_COLORS[p.phase] || "#94A3B8" }}
                        >
                          {PHASE_LABELS[p.phase] || p.phase}
                        </span>
                      </div>
                      <p className="text-xs truncate mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>
                        {p.company} · {p.indication}
                      </p>
                    </div>
                    <span className="text-[10px] text-right max-w-[120px] leading-tight hidden sm:block" style={{ color: "var(--clr-text-secondary)" }}>
                      {p.mechanism}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
