import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import AgentInsightBar from '@/components/AgentInsightBar'
import { ArrowLeft, CheckCircle, XCircle, FileText } from 'lucide-react'
import InspectionScoreModal from '@/components/InspectionScoreModal'
import { fetchHistory, confirmTask } from '@/api/inspection'
import type { InspectionTask } from '@/types/inspection'

export default function InspectionReview() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<InspectionTask[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState<InspectionTask | null>(null)
  const [showScore, setShowScore] = useState(false)
  const [reviewEvidence, setReviewEvidence] = useState('')
  const [reviewResult, setReviewResult] = useState<unknown>(null)

  useEffect(() => {
    let cancelled = false
    fetchHistory().then(data => {
      if (!cancelled) setTasks(data.filter((t: InspectionTask) => t.capa_stage !== 'scoring'))
    }).finally(() => setLoading(false))
    return () => { cancelled = true }
  }, [])

  async function handleConfirm(task: InspectionTask) {
    const evidence = reviewEvidence || 'remediation-evidence'
    const res = await confirmTask(task.inspection_id || 'task-cold-chain-001', evidence)
    setReviewResult(res)
    setShowScore(true)
  }

  function handleScoreComplete() {
    setShowScore(false)
    setSelectedTask(null)
    setReviewEvidence('')
  }

  return (
    <div className="space-y-4">
      <AgentInsightBar pageId="manager_review" />
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/manager/inspection')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> 返回
        </Button>
        <div>
          <h2 className="text-lg font-semibold">复查确认</h2>
          <p className="text-sm text-muted-foreground">代表提交整改证据，经理确认通过或驳回</p>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground py-8 text-center">加载中...</p>
      ) : tasks.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center">暂无待复查的整改任务</p>
      ) : (
        <div className="space-y-3">
          {tasks.map((task: InspectionTask, i: number) => {
            const taskId = task.inspection_id || task.id || `task-${i}`
            return (
              <Card key={taskId}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                        <p className="text-sm font-medium truncate">{task.event || task.title || `整改 ${taskId}`}</p>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span>负责人: {task.owner || '-'}</span>
                        <span>阶段: {task.capa_stage || '待复查'}</span>
                        <span>得分: {task.score ?? '-'}</span>
                      </div>
                    </div>
                  </div>

                  {selectedTask?.inspection_id === task.inspection_id && (
                    <div className="mt-3 pt-3 border-t space-y-3">
                      <div className="space-y-1">
                        <Label className="text-xs">整改证据说明</Label>
                        <Input
                          value={reviewEvidence}
                          onChange={e => setReviewEvidence(e.target.value)}
                          placeholder="输入整改证据描述或文件路径"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleConfirm(task)}>
                          <CheckCircle className="h-3 w-3 mr-1" /> 确认通过
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { setSelectedTask(null); setReviewEvidence('') }}>
                          <XCircle className="h-3 w-3 mr-1" /> 驳回
                        </Button>
                      </div>
                      {reviewResult && (
                        <p className="text-xs text-green-600">复查已确认，请完成评分</p>
                      )}
                    </div>
                  )}

                  <div className="mt-2">
                    <Button variant="ghost" size="sm" onClick={() => setSelectedTask(selectedTask?.inspection_id === task.inspection_id ? null : task)}>
                      {selectedTask?.inspection_id === task.inspection_id ? '收起' : '复查'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {showScore && (
        <InspectionScoreModal
          taskId={selectedTask?.inspection_id || 'inspection-2026-06'}
          onClose={handleScoreComplete}
        />
      )}
    </div>
  )
}
