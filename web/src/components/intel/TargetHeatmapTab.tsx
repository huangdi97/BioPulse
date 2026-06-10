import { useState, useEffect, useMemo } from "react"
import { X } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Card, CardContent } from "../ui/Card"
import { Button } from "../ui/Button"
import { getIntelTargets, getIntelTargetCategories } from "../../api/client"
import PipelineAssociation from "./PipelineAssociation"
import type { Target } from "../../types/intel"

const CHART_COLORS = ['#0f62fe', '#8b5cf6', '#f59e0b', '#10b981', '#da1e28', '#24a148', '#f1c21b', '#525252', '#002d9c', '#6f6f6f']

export default function TargetHeatmapTab() {
  const [categoryFilter, setCategoryFilter] = useState('全部')
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null)
  const [sortKey, setSortKey] = useState('paper_count')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [targets, setTargets] = useState<Target[]>([])
  const [targetCategories, setTargetCategories] = useState<string[]>(['全部'])

  useEffect(() => {
getIntelTargetCategories().then(data => {
      setTargetCategories(data)
    })
  }, [])

  useEffect(() => {
    const category = categoryFilter === '全部' ? '' : categoryFilter
    getIntelTargets(category, sortKey, sortDir).then(data => {
      setTargets(data)
    })
  }, [categoryFilter, sortKey, sortDir])

  const chartData = useMemo(() => {
    if (targets.length === 0) return []
    const months = targets[0].trend_data.map(td => td.month)
    return months.map(month => {
      const point: Record<string, string | number> = { month: month.slice(5) + '月' }
      targets.forEach(t => {
        const td = t.trend_data.find(d => d.month === month)
        if (td) point[t.name] = td.count
      })
      return point
    })
  }, [targets])

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  function sortIcon(key: string) {
    if (sortKey !== key) return ''
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium" style={{color: 'var(--clr-text-secondary)'}}>靶点类别:</label>
        <select
          value={categoryFilter}
          onChange={e => setCategoryFilter(e.target.value)}
          className="h-9 rounded-md border px-3 text-sm bg-white"
          style={{borderColor: 'var(--clr-border-default)', color: 'var(--clr-text-primary)'}}
        >
          {targetCategories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <Card>
        <CardContent className="p-5">
          <h3 className="text-sm font-semibold mb-4" style={{color: 'var(--clr-text-primary)'}}>论文数量趋势 (近12个月)</h3>
          {targets.length === 0 ? (
            <p className="text-center py-8 text-sm" style={{color: 'var(--clr-text-secondary)'}}>暂无数据</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-gray-20)" />
                <XAxis dataKey="month" tick={{fontSize: 11, fill: 'var(--clr-text-secondary)'}} stroke="var(--clr-gray-30)" />
                <YAxis tick={{fontSize: 11, fill: 'var(--clr-text-secondary)'}} stroke="var(--clr-gray-30)" />
                <Tooltip contentStyle={{background: 'var(--clr-white)', border: '1px solid var(--clr-gray-20)', borderRadius: 6, fontSize: 12}} />
                <Legend />
                {targets.map((t, i) => (
                  <Line key={t.id} type="monotone" dataKey={t.name} stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={{r: 2}} name={t.name} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {selectedTarget ? (
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold" style={{color: 'var(--clr-text-primary)'}}>{selectedTarget.name} - 详细数据</h4>
              <Button variant="ghost" size="sm" onClick={() => setSelectedTarget(null)}><X className="w-3 h-3" /> 关闭</Button>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={selectedTarget.trend_data.map(td => ({...td, month: td.month.slice(5) + '月'}))}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-gray-20)" />
                <XAxis dataKey="month" tick={{fontSize: 11, fill: 'var(--clr-text-secondary)'}} />
                <YAxis tick={{fontSize: 11, fill: 'var(--clr-text-secondary)'}} />
                <Tooltip contentStyle={{background: 'var(--clr-white)', border: '1px solid var(--clr-gray-20)', borderRadius: 6, fontSize: 12}} />
                <Line type="monotone" dataKey="count" stroke="#0f62fe" strokeWidth={2} dot={{r: 3}} name="论文数" />
              </LineChart>
            </ResponsiveContainer>
            <div className="flex gap-4 text-xs" style={{color: 'var(--clr-text-secondary)'}}>
              <span>年论文数: {selectedTarget.paper_count.toLocaleString()}</span>
              <span>临床试验: {selectedTarget.trial_count.toLocaleString()}</span>
              <span>增长率: <span style={{color: selectedTarget.growth >= 0 ? 'var(--clr-success)' : 'var(--clr-error)'}}>{selectedTarget.growth > 0 ? '+' : ''}{selectedTarget.growth}%</span></span>
            </div>
            <PipelineAssociation targetId={selectedTarget.id} targetName={selectedTarget.name} />
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-lg overflow-hidden border" style={{borderColor: 'var(--clr-border-default)'}}>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b" style={{borderColor: 'var(--clr-gray-20)'}}>
                {[
                  { key: 'name', label: '靶点名称', sortable: false },
                  { key: 'category', label: '类别', sortable: false },
                  { key: 'paper_count', label: '年论文数', sortable: true },
                  { key: 'trial_count', label: '临床试验数', sortable: true },
                  { key: 'growth', label: '增长率', sortable: true },
                ].map(h => (
                  <th
                    key={h.key}
                    className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${h.sortable ? 'cursor-pointer select-none' : ''}`}
                    style={{color: 'var(--clr-text-secondary)'}}
                    onClick={() => h.sortable && handleSort(h.key)}
                  >
                    {h.label}{h.sortable ? sortIcon(h.key) : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {targets.map(t => (
                <tr
                  key={t.id}
                  className="border-b last:border-0 cursor-pointer transition-colors hover:bg-[var(--clr-surface-hover)]"
                  style={{borderColor: 'var(--clr-gray-20)'}}
                  onClick={() => setSelectedTarget(t)}
                >
                  <td className="px-4 py-3 font-medium" style={{color: 'var(--clr-text-primary)'}}>{t.name}</td>
                  <td className="px-4 py-3" style={{color: 'var(--clr-text-secondary)'}}>{t.category}</td>
                  <td className="px-4 py-3" style={{color: 'var(--clr-text-primary)'}}>{t.paper_count.toLocaleString()}</td>
                  <td className="px-4 py-3" style={{color: 'var(--clr-text-primary)'}}>{t.trial_count.toLocaleString()}</td>
                  <td className="px-4 py-3" style={{color: t.growth >= 0 ? 'var(--clr-success)' : 'var(--clr-error)'}}>{t.growth > 0 ? '+' : ''}{t.growth}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
