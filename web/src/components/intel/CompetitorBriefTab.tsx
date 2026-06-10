import { useState, useEffect } from "react"
import { Card, CardContent } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { Button } from "../ui/Button"
import { getCompetitorBriefLatest, getCompetitorBrief, generateCompetitorBrief } from "../../api/client"

const RISK_COLOR: Record<string, string> = { low: 'var(--clr-success)', medium: 'var(--clr-warning)', high: 'var(--clr-error)' }
const RISK_LABEL: Record<string, string> = { low: '低', medium: '中', high: '高' }

export default function CompetitorBriefTab() {
  const [brief, setBrief] = useState<any>(null)
  const [briefList, setBriefList] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    getCompetitorBriefLatest().then(d => {
      if (d) {
        setBrief(d)
        setBriefList([d])
        setSelectedId(d.id)
      }
      setLoading(false)
    })
  }, [])

  function handleGenerate() {
    setGenerating(true)
    generateCompetitorBrief().then(d => {
      if (d) {
        setBrief(d)
        setBriefList(prev => [d, ...prev])
        setSelectedId(d.id)
      }
      setGenerating(false)
    })
  }

  function handleSelect(id: string) {
    setSelectedId(id)
    const existing = briefList.find(b => b.id === id)
    if (existing) {
      setBrief(existing)
    } else {
      setLoading(true)
      getCompetitorBrief(id).then(d => {
        if (d) {
          setBrief(d)
          setBriefList(prev => [d, ...prev])
        }
        setLoading(false)
      })
    }
  }

  if (loading) return <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--clr-text-primary)' }}>竞品简报</h3>
        <Button onClick={handleGenerate} disabled={generating}>
          {generating ? '生成中...' : '生成新简报'}
        </Button>
      </div>

      {brief ? (
        <>
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium" style={{ color: 'var(--clr-text-primary)' }}>{brief.title}</h4>
                  <p className="text-xs mt-1" style={{ color: 'var(--clr-text-secondary)' }}>
                    {brief.generated_at ? new Date(brief.generated_at).toLocaleString('zh-CN') : ''}
                  </p>
                </div>
                {brief.risk_level && (
                  <Badge style={{ backgroundColor: RISK_COLOR[brief.risk_level] || 'var(--clr-gray-30)', color: '#fff' }}>
                    风险: {RISK_LABEL[brief.risk_level] || brief.risk_level}
                  </Badge>
                )}
              </div>

              {brief.highlights && brief.highlights.length > 0 && (
                <div>
                  <p className="text-xs font-medium mb-1" style={{ color: 'var(--clr-text-secondary)' }}>高亮摘要</p>
                  <ul className="space-y-1">
                    {brief.highlights.map((h: string, i: number) => (
                      <li key={i} className="text-xs pl-3 relative" style={{ color: 'var(--clr-text-primary)' }}>
                        <span className="absolute left-0 top-0">•</span>
                        {h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {brief.comparison && (
                <details>
                  <summary className="text-xs cursor-pointer font-medium" style={{ color: 'var(--clr-brand)' }}>
                    查看对比详情
                  </summary>
                  <div className="mt-2 text-xs space-y-1" style={{ color: 'var(--clr-text-secondary)' }}>
                    {brief.comparison.items?.map((item: any) => (
                      <p key={item.product_id}>{item.product_name}: 价格指数={item.price_index}, 情绪指数={item.sentiment_index}</p>
                    ))}
                  </div>
                </details>
              )}

              {brief.strategy?.suggestions && (
                <div>
                  <p className="text-xs font-medium mb-1" style={{ color: 'var(--clr-text-secondary)' }}>策略建议</p>
                  <div className="space-y-2">
                    {brief.strategy.suggestions.map((s: any, i: number) => (
                      <div key={i} className="p-2 rounded text-xs" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                        <div className="flex items-center gap-2 mb-1">
                          <Badge style={{ backgroundColor: s.priority === 'high' ? 'var(--clr-error)' : 'var(--clr-warning)', color: '#fff', fontSize: 10 }}>
                            {s.priority === 'high' ? '高优先级' : '中优先级'}
                          </Badge>
                          <span className="font-medium" style={{ color: 'var(--clr-text-primary)' }}>{s.theme}</span>
                        </div>
                        <p style={{ color: 'var(--clr-text-secondary)' }}>{s.action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {briefList.length > 1 && (
            <Card>
              <CardContent className="p-4">
                <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--clr-text-secondary)' }}>历史简报</h4>
                <div className="space-y-1">
                  {briefList.map(b => (
                    <button
                      key={b.id}
                      onClick={() => handleSelect(b.id)}
                      className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                        selectedId === b.id ? 'bg-[var(--clr-gray-20)]' : 'hover:bg-[var(--clr-gray-10)]'
                      }`}
                      style={{ color: selectedId === b.id ? 'var(--clr-text-primary)' : 'var(--clr-text-secondary)' }}
                    >
                      <span className="font-medium">{b.title}</span>
                      <span className="ml-2">{b.generated_at ? new Date(b.generated_at).toLocaleDateString('zh-CN') : ''}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>暂无简报，点击「生成新简报」创建</p>
      )}
    </div>
  )
}
