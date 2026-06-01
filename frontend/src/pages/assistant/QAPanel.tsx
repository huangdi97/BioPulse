import { useState } from 'react'
import { postQA } from '@/api/assistant-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { MessageSquare, Send } from 'lucide-react'

export default function QAPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAsk = async () => {
    if (!question.trim()) return
    setLoading(true)
    const res = await postQA(question)
    setAnswer(res.answer)
    setLoading(false)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">智能问答</h2>
      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><MessageSquare className="h-4 w-4 text-teal-600" />向AI提问</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="请输入您的问题..."
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            />
            <Button onClick={handleAsk} disabled={loading || !question.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
          {answer && (
            <div className="p-4 rounded-lg bg-teal-50">
              <p className="text-xs font-medium text-teal-700 mb-1">AI 回答</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{answer}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
