import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Star } from 'lucide-react'

interface Props {
  taskId: string
  onClose: () => void
}

const DIMENSIONS = [
  { key: 'compliance', label: '合规性评分', desc: '整改是否符合合规要求' },
  { key: 'timeliness', label: '及时性评分', desc: '整改是否在期限内完成' },
  { key: 'completeness', label: '完整性评分', desc: '整改证据是否完整充分' },
]

export default function InspectionScoreModal({ taskId, onClose }: Props) {
  const [scores, setScores] = useState<Record<string, number>>({
    compliance: 0,
    timeliness: 0,
    completeness: 0,
  })
  const [notes, setNotes] = useState('')
  const [submitted, setSubmitted] = useState(false)

  function setScore(dim: string, val: number) {
    setScores(s => ({ ...s, [dim]: Math.max(0, Math.min(100, val)) }))
  }

  const total = Math.round(
    (scores.compliance * 0.4 + scores.timeliness * 0.3 + scores.completeness * 0.3)
  )

  function handleSubmit() {
    setSubmitted(true)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-500" /> CAPA评分
          </CardTitle>
          <p className="text-xs text-muted-foreground">任务ID: {taskId}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {DIMENSIONS.map(dim => (
            <div key={dim.key} className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="text-xs">{dim.label}</Label>
                <span className="text-xs font-mono">{scores[dim.key]}分</span>
              </div>
              <p className="text-xs text-muted-foreground">{dim.desc}</p>
              <div className="flex items-center gap-2">
                <Input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={scores[dim.key]}
                  onChange={e => setScore(dim.key, parseInt(e.target.value))}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={scores[dim.key]}
                  onChange={e => setScore(dim.key, parseInt(e.target.value) || 0)}
                  className="w-16 text-xs"
                />
              </div>
            </div>
          ))}

          <div className="rounded-lg bg-muted p-3 text-center">
            <p className="text-xs text-muted-foreground">综合评分</p>
            <p className={`text-2xl font-bold ${total >= 80 ? 'text-green-600' : total >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
              {total}
            </p>
            <div className="w-full bg-border rounded-full h-2 mt-1">
              <div
                className={`h-2 rounded-full transition-all ${
                  total >= 80 ? 'bg-green-500' : total >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${total}%` }}
              />
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs">评分备注</Label>
            <Input
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="可选：补充评分说明"
            />
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <Button variant="outline" onClick={onClose}>关闭</Button>
            <Button onClick={handleSubmit} disabled={submitted}>
              {submitted ? '已提交' : '提交评分'}
            </Button>
          </div>

          {submitted && (
            <div className="rounded-lg bg-green-50 text-green-700 p-3 text-xs text-center">
              评分已提交。合规性 {scores.compliance}分 / 及时性 {scores.timeliness}分 / 完整性 {scores.completeness}分
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
