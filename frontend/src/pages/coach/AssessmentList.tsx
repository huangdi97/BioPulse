import { useState, useEffect } from 'react'
import { fetchAssessments, type Assessment } from '@/api/coach'
import { Card, CardContent } from '@/components/ui/card'
import { Star } from 'lucide-react'

export default function AssessmentList() {
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchAssessments().then((data) => {
      if (cancelled) return
      setAssessments(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-24 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">评估结果</h2>
      {assessments.map((a) => (
        <Card key={a.id}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm font-semibold">{a.sessionName}</p>
                <p className="text-xs text-muted-foreground">{a.createdAt}</p>
              </div>
              <div className="flex items-center gap-1">
                <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                <span className="text-lg font-bold">{a.overallScore}</span>
                <span className="text-xs text-muted-foreground">分</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {[
                { label: '沟通', value: a.communicationScore },
                { label: '产品', value: a.productKnowledgeScore },
                { label: '合规', value: a.complianceScore },
              ].map((item) => (
                <div key={item.label} className="text-center p-2 rounded bg-muted/50">
                  <p className="text-xs text-muted-foreground">{item.label}</p>
                  <p className="text-sm font-bold">{item.value}</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground bg-muted/30 p-2 rounded">{a.feedback}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
