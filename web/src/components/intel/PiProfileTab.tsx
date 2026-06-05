import { useState, useMemo } from "react"
import { Card, CardContent } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { Button } from "../ui/Button"
import { Input } from "../ui/Input"
import { piProfiles } from "../../api/mockIntel"

export default function PiProfileTab() {
  const [piQuery, setPiQuery] = useState('')
  const [selectedPi, setSelectedPi] = useState<number | null>(null)

  const filteredPis = useMemo(() => {
    if (!piQuery.trim()) return piProfiles
    const q = piQuery.toLowerCase()
    return piProfiles.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.institution.toLowerCase().includes(q) ||
      p.research_areas.some(a => a.toLowerCase().includes(q))
    )
  }, [piQuery])

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="搜索PI姓名、机构..."
          value={piQuery}
          onChange={e => setPiQuery(e.target.value)}
        />
        <Button>搜索</Button>
      </div>
      {filteredPis.length === 0 ? (
        <p className="text-center py-8 text-sm" style={{color: 'var(--clr-text-secondary)'}}>未找到相关PI</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPis.map(pi => (
            <Card key={pi.id} className="cursor-pointer" onClick={() => setSelectedPi(selectedPi === pi.id ? null : pi.id)}>
              <CardContent className="p-4 space-y-2">
                <h4 className="font-semibold" style={{color: 'var(--clr-text-primary)'}}>{pi.name}</h4>
                <p className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>{pi.institution} | {pi.title}</p>
                <p className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>{pi.department}</p>
                <div className="flex items-end gap-1">
                  <span className="text-2xl font-bold" style={{color: 'var(--clr-brand)'}}>{pi.h_index}</span>
                  <span className="text-xs mb-1" style={{color: 'var(--clr-text-secondary)'}}>H-index</span>
                </div>
                <div className="flex gap-1 flex-wrap">
                  {pi.research_areas.map(a => <Badge key={a}>{a}</Badge>)}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>活跃度: {pi.activity_score}%</span>
                  <div className="flex-1 h-1.5 rounded-full" style={{backgroundColor: 'var(--clr-gray-20)'}}>
                    <div className="h-full rounded-full" style={{width: `${pi.activity_score}%`, backgroundColor: 'var(--clr-mode-research)'}} />
                  </div>
                </div>
                {selectedPi === pi.id && (
                  <div className="text-xs space-y-1 p-2 rounded mt-1" style={{color: 'var(--clr-text-secondary)', backgroundColor: 'var(--clr-gray-10)'}}>
                    <p>论文总数: {pi.papers}</p>
                    <p>基金: {pi.grants.join('、')}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
