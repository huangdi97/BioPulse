import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { fetchExclusionGates } from '@/api/adminPresident'

export default function ExclusionGateConfig() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchExclusionGates>> | null>(null)
  const [gates, setGates] = useState<Awaited<ReturnType<typeof fetchExclusionGates>>['gates']>([])

  useEffect(() => {
    let cancelled = false
    fetchExclusionGates().then((d) => { if (!cancelled) { setData(d); setGates(d.gates) } })
    return () => { cancelled = true }
  }, [])

  const toggleGate = (id: number) => {
    setGates((prev) => prev.map((g) => (g.id === id ? { ...g, enabled: !g.enabled } : g)))
  }

  if (!data) return <div className="p-4 text-muted-foreground">加载中...</div>

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-base">排除闸配置</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">管理合规规则例外情况，配置豁免条件和作用范围。</p>
          <div className="space-y-2">
            {gates.map((g) => (
              <div key={g.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{g.name}</p>
                  <p className="text-xs text-muted-foreground">规则: {g.rule} / 范围: {g.scope}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge variant={g.enabled ? 'default' : 'secondary'}>{g.enabled ? '已启用' : '已禁用'}</Badge>
                  <button
                    onClick={() => toggleGate(g.id)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${g.enabled ? 'bg-primary' : 'bg-gray-300'}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${g.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
