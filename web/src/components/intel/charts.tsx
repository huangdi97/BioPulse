function Bar({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 shrink-0 text-right" style={{ color: 'var(--clr-text-secondary)' }}>{label}</span>
      <div className="flex-1 h-4 rounded-sm" style={{ backgroundColor: 'var(--clr-gray-20)' }}>
        <div className="h-full rounded-sm transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="w-10 shrink-0 font-medium" style={{ color: 'var(--clr-text-primary)' }}>{value}</span>
    </div>
  )
}

function MiniLineChart({ data, color, height = 60 }: { data: { label: string; value: number }[]; color: string; height?: number }) {
  if (data.length === 0) return null
  const max = Math.max(...data.map(d => d.value), 1)
  const w = 280
  const h = height
  const padL = 0
  const padR = 0
  const padT = 4
  const padB = 4
  const chartW = w - padL - padR
  const chartH = h - padT - padB
  const stepX = chartW / (data.length - 1 || 1)
  const points = data.map((d, i) => `${padL + i * stepX},${padT + chartH - (d.value / max) * chartH}`).join(' ')
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ maxHeight: h }}>
      <polyline fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" points={points} />
      {data.map((d, i) => (
        <circle key={i} cx={padL + i * stepX} cy={padT + chartH - (d.value / max) * chartH} r="2.5" fill={color} />
      ))}
    </svg>
  )
}

function MiniBarChart({ data, height = 80 }: { data: { label: string; positive: number; negative: number; neutral: number }[]; height?: number }) {
  if (data.length === 0) return null
  const max = Math.max(...data.flatMap(d => [d.positive, d.neutral, d.negative]), 1)
  const w = 300
  const h = height
  const barGap = 2
  const barW = Math.max(4, Math.min(12, (w - barGap * data.length) / data.length / 3 - 1))
  const padB = 12
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ maxHeight: h }}>
      {data.map((d, i) => {
        const xBase = i * (barW * 3 + barGap * 3 + 2)
        const xPos = xBase
        const xNeu = xBase + barW + 1
        const xNeg = xBase + barW * 2 + 2
        const hPos = (d.positive / max) * (h - padB)
        const hNeu = (d.neutral / max) * (h - padB)
        const hNeg = (d.negative / max) * (h - padB)
        return (
          <g key={i}>
            <rect x={xPos} y={h - padB - hPos} width={barW} height={hPos} fill="#10b981" rx={1} />
            <rect x={xNeu} y={h - padB - hNeu} width={barW} height={hNeu} fill="#6b7280" rx={1} />
            <rect x={xNeg} y={h - padB - hNeg} width={barW} height={hNeg} fill="#ef4444" rx={1} />
          </g>
        )
      })}
    </svg>
  )
}

export { Bar, MiniLineChart, MiniBarChart }
