import { useState, useEffect } from "react"
import { Card, CardContent } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { Button } from "../ui/Button"
import { MiniLineChart, MiniBarChart } from "./charts"
import {
  getCompetitorProducts,
  getCompetitorSentiment,
  getCompetitorVolume,
  getCompetitorPriceAnomaly,
  getCompetitorCompare,
} from "../../api/client"

const SUB_TABS = ['竞品总览', '舆情情绪', '声量趋势', '价格异动', '竞品对比']

const STATUS_LABEL: Record<string, string> = { active: '活跃', watchlist: '观察', inactive: '停用' }
const STATUS_COLOR: Record<string, string> = { active: 'var(--clr-success)', watchlist: 'var(--clr-warning)', inactive: 'var(--clr-error)' }
const CATEGORY_LABEL: Record<string, string> = { cardiovascular: '心血管', oncology: '肿瘤', cns: '中枢神经', metabolic: '代谢' }

function ProductOverview() {
  const [products, setProducts] = useState<any[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCompetitorProducts().then(data => { setProducts(data); setLoading(false) })
  }, [])

  if (loading) return <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
  if (products.length === 0) return <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂无产品数据</p>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {products.map(p => (
        <Card key={p.id} className="cursor-pointer" onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-start justify-between">
              <h4 className="text-sm font-medium" style={{ color: 'var(--clr-text-primary)' }}>{p.name}</h4>
              <Badge style={{ backgroundColor: STATUS_COLOR[p.status] || 'var(--clr-gray-30)', color: '#fff' }}>
                {STATUS_LABEL[p.status] || p.status}
              </Badge>
            </div>
            <p className="text-xs" style={{ color: 'var(--clr-text-secondary)' }}>{p.company}</p>
            <p className="text-xs" style={{ color: 'var(--clr-text-secondary)' }}>
              {CATEGORY_LABEL[p.category] || p.category} | {p.indication}
            </p>
            <div className="flex gap-1 flex-wrap text-xs">
              <span style={{ color: 'var(--clr-text-secondary)' }}>覆盖:</span>
              {p.province_coverage?.map((prov: string) => (
                <span key={prov} className="px-1.5 py-0.5 rounded text-xs" style={{ backgroundColor: 'var(--clr-gray-10)', color: 'var(--clr-text-secondary)' }}>
                  {prov}
                </span>
              ))}
            </div>
            {expandedId === p.id && (
              <div className="text-xs space-y-1 p-2 rounded mt-1" style={{ color: 'var(--clr-text-secondary)', backgroundColor: 'var(--clr-gray-10)' }}>
                <p>ID: {p.id}</p>
                <p>适应症: {p.indication}</p>
                <p>覆盖省份数: {p.province_coverage?.length || 0}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function SentimentPanel() {
  const [keyword, setKeyword] = useState('瑞舒伐他汀')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  function load() {
    setLoading(true)
    getCompetitorSentiment(keyword, 30).then(d => { setData(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const summary = data?.summary
  const trend: any[] = data?.trend || []

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          className="h-9 rounded-md border px-3 text-sm flex-1 bg-white"
          style={{ borderColor: 'var(--clr-border-default)', color: 'var(--clr-text-primary)' }}
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          placeholder="输入关键词"
        />
        <Button onClick={load}>分析</Button>
      </div>
      {loading ? (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
      ) : summary ? (
        <>
          <Card>
            <CardContent className="p-4">
              <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--clr-text-primary)' }}>情绪概览</h4>
              <div className="flex gap-4 text-sm mb-3">
                <span>总提及: <strong>{summary.mentions}</strong></span>
                <span style={{ color: '#10b981' }}>正面: <strong>{summary.positive}</strong></span>
                <span style={{ color: '#6b7280' }}>中性: <strong>{summary.neutral}</strong></span>
                <span style={{ color: '#ef4444' }}>负面: <strong>{summary.negative}</strong></span>
                <span>情绪分: <strong>{summary.sentiment_score}</strong></span>
              </div>
              <div className="flex gap-1 h-4 rounded overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: `${(summary.positive / summary.mentions) * 100}%` }} />
                <div className="h-full bg-gray-400" style={{ width: `${(summary.neutral / summary.mentions) * 100}%` }} />
                <div className="h-full bg-red-500" style={{ width: `${(summary.negative / summary.mentions) * 100}%` }} />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--clr-text-primary)' }}>情绪趋势 (30天)</h4>
              <MiniBarChart data={trend.map(d => ({ label: d.date, positive: d.positive, negative: d.negative, neutral: d.neutral }))} height={100} />
              <div className="flex justify-center gap-4 mt-2 text-xs" style={{ color: 'var(--clr-text-secondary)' }}>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-green-500 inline-block" /> 正面</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-gray-400 inline-block" /> 中性</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-red-500 inline-block" /> 负面</span>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂无情绪数据</p>
      )}
    </div>
  )
}

function VolumePanel() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCompetitorVolume().then(d => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
  if (!data) return <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂无数据</p>

  const series: any[] = data.series || []

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--clr-text-primary)' }}>声量趋势 (近7天 · {data.platform})</h4>
          <MiniLineChart data={series.map(s => ({ label: s.date.slice(5), value: s.mentions }))} color="#0f62fe" height={80} />
          <div className="grid grid-cols-7 gap-1 mt-2">
            {series.map(s => (
              <div key={s.date} className="text-center">
                <div className="text-xs font-medium" style={{ color: 'var(--clr-text-primary)' }}>{s.mentions}</div>
                <div className="text-xs" style={{ color: 'var(--clr-text-secondary)' }}>{s.date.slice(5)}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function PriceAnomalyPanel() {
  const [productId, setProductId] = useState('prod-001')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  function load() {
    setLoading(true)
    getCompetitorPriceAnomaly(productId).then(d => { setData(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const anomalies: any[] = data?.anomalies || []

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>产品:</label>
        <select
          value={productId}
          onChange={e => setProductId(e.target.value)}
          className="h-9 rounded-md border px-3 text-sm bg-white"
          style={{ borderColor: 'var(--clr-border-default)', color: 'var(--clr-text-primary)' }}
        >
          <option value="prod-001">瑞舒伐他汀钙片</option>
          <option value="prod-002">阿托伐他汀钙片</option>
          <option value="prod-003">依折麦布片</option>
        </select>
        <Button onClick={load}>查询</Button>
      </div>
      {loading ? (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
      ) : data ? (
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex gap-4 text-sm">
              <span style={{ color: 'var(--clr-text-secondary)' }}>基线价格: <strong style={{ color: 'var(--clr-text-primary)' }}>{data.baseline_price} CNY</strong></span>
              <span style={{ color: 'var(--clr-text-secondary)' }}>异常记录: <strong style={{ color: 'var(--clr-text-primary)' }}>{anomalies.length}</strong></span>
            </div>
            {anomalies.length === 0 ? (
              <p className="text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂未检测到价格异常</p>
            ) : (
              <div className="rounded-lg overflow-hidden border" style={{ borderColor: 'var(--clr-border-default)' }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b" style={{ borderColor: 'var(--clr-gray-20)' }}>
                      <th className="px-3 py-2 text-left text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>日期</th>
                      <th className="px-3 py-2 text-left text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>省份</th>
                      <th className="px-3 py-2 text-right text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>价格</th>
                      <th className="px-3 py-2 text-right text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>偏差</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.map((a, i) => (
                      <tr key={i} className="border-b last:border-0" style={{ borderColor: 'var(--clr-gray-20)' }}>
                        <td className="px-3 py-2" style={{ color: 'var(--clr-text-primary)' }}>{a.date}</td>
                        <td className="px-3 py-2" style={{ color: 'var(--clr-text-secondary)' }}>{a.province}</td>
                        <td className="px-3 py-2 text-right font-medium" style={{ color: 'var(--clr-text-primary)' }}>{a.price}</td>
                        <td className="px-3 py-2 text-right" style={{ color: a.delta_pct < 0 ? 'var(--clr-error)' : 'var(--clr-success)' }}>
                          {a.delta_pct > 0 ? '+' : ''}{a.delta_pct}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂无数据</p>
      )}
    </div>
  )
}

function ComparePanel() {
  const [selected, setSelected] = useState<string[]>(['prod-001', 'prod-002'])
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  function toggle(id: string) {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  function doCompare() {
    if (selected.length < 2) return
    setLoading(true)
    getCompetitorCompare(selected.join(',')).then(d => { setData(d); setLoading(false) })
  }

  const items: any[] = data?.items || []
  const leaders: Record<string, string> = data?.leaders || {}

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center flex-wrap">
        <span className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>选择产品(至少2个):</span>
        {['prod-001', 'prod-002', 'prod-003'].map(id => {
          const names: Record<string, string> = { 'prod-001': '瑞舒伐他汀', 'prod-002': '阿托伐他汀', 'prod-003': '依折麦布' }
          return (
            <label key={id} className="flex items-center gap-1 text-sm cursor-pointer">
              <input type="checkbox" checked={selected.includes(id)} onChange={() => toggle(id)} className="accent-[var(--clr-brand)]" />
              <span style={{ color: 'var(--clr-text-primary)' }}>{names[id]}</span>
            </label>
          )
        })}
        <Button onClick={doCompare} disabled={selected.length < 2}>对比</Button>
      </div>
      {loading ? (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
      ) : items.length > 0 ? (
        <Card>
          <CardContent className="p-4 space-y-4">
            <h4 className="text-sm font-semibold" style={{ color: 'var(--clr-text-primary)' }}>产品对比</h4>
            <div className="rounded-lg overflow-hidden border" style={{ borderColor: 'var(--clr-border-default)' }}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--clr-gray-20)' }}>
                    <th className="px-3 py-2 text-left text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>维度</th>
                    {items.map(i => (
                      <th key={i.product_id} className="px-3 py-2 text-center text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>
                        {i.product_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: 'price_index', label: '价格指数' },
                    { key: 'sentiment_index', label: '情绪指数' },
                    { key: 'access_index', label: '准入指数' },
                    { key: 'coverage_count', label: '覆盖省份' },
                    { key: 'risk_level', label: '风险等级' },
                  ].map(row => (
                    <tr key={row.key} className="border-b last:border-0" style={{ borderColor: 'var(--clr-gray-20)' }}>
                      <td className="px-3 py-2 text-xs font-medium" style={{ color: 'var(--clr-text-primary)' }}>{row.label}</td>
                      {items.map(i => {
                        const val = i[row.key]
                        const isLeader = leaders[row.key.replace('_index', '')] === i.product_id
                        return (
                          <td key={i.product_id} className="px-3 py-2 text-center text-xs" style={{ color: isLeader ? 'var(--clr-brand)' : 'var(--clr-text-secondary)', fontWeight: isLeader ? 600 : 400 }}>
                            {row.key === 'risk_level' ? (STATUS_LABEL[val] || val) : val}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data?.leaders && (
              <div className="text-xs space-y-1" style={{ color: 'var(--clr-text-secondary)' }}>
                <p>🏆 最低价: {items.find(i => i.product_id === leaders.price)?.product_name}</p>
                <p>🏆 最佳情绪: {items.find(i => i.product_id === leaders.sentiment)?.product_name}</p>
                <p>🏆 最佳准入: {items.find(i => i.product_id === leaders.access)?.product_name}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ) : selected.length >= 2 && !loading ? (
        <p className="text-center py-4 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>点击「对比」查看结果</p>
      ) : null}
    </div>
  )
}

export default function CompetitorIntelTab() {
  const [subTab, setSubTab] = useState(0)

  return (
    <div className="space-y-4">
      <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
        {SUB_TABS.map((t, i) => (
          <button
            key={t}
            onClick={() => setSubTab(i)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              i === subTab ? 'bg-white shadow-sm font-medium' : ''
            }`}
            style={{ color: i === subTab ? 'var(--clr-text-primary)' : 'var(--clr-text-secondary)' }}
          >
            {t}
          </button>
        ))}
      </div>

      {subTab === 0 && <ProductOverview />}
      {subTab === 1 && <SentimentPanel />}
      {subTab === 2 && <VolumePanel />}
      {subTab === 3 && <PriceAnomalyPanel />}
      {subTab === 4 && <ComparePanel />}
    </div>
  )
}
