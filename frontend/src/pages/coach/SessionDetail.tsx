import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchSessionDetail, type Session } from '@/api/coach'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Clock, MessageSquare } from 'lucide-react'

interface DialogueEntry {
  role: 'rep' | 'ai' | 'system'
  content: string
  timestamp: string
}

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    fetchSessionDetail(parseInt(id)).then((data) => {
      if (cancelled) return
      setSession(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [id])

  const dialogues: DialogueEntry[] = [
    { role: 'system', content: '场景开始：你正在拜访一位心内科主任，目标是推广新药。', timestamp: '00:00' },
    { role: 'rep', content: '张主任您好，感谢您在百忙之中接待我。今天想跟您分享一下我们新上市的抗凝药物。', timestamp: '00:15' },
    { role: 'ai', content: '（微笑）你好，请坐。最近确实有听说这款新药，但还不太了解，你简单介绍下吧。', timestamp: '00:30' },
    { role: 'rep', content: '好的。这款新药在大型临床试验中表现出色，相比现有方案，可降低卒中风险30%，同时出血风险更低。', timestamp: '01:00' },
    { role: 'ai', content: '数据听起来不错。不过价格方面呢？比我们目前用的要贵不少吧？', timestamp: '01:30' },
    { role: 'rep', content: '确实，单价略高。但从成本效益分析来看，考虑到减少了不良事件和住院率，整体治疗成本反而更低。这里有详细的药物经济学数据。', timestamp: '02:00' },
    { role: 'ai', content: '嗯，有理有据。你先把资料留下，我和科室同事再讨论一下。', timestamp: '02:30' },
    { role: 'system', content: '场景结束。', timestamp: '03:00' },
  ]

  if (loading) {
    return <div className="space-y-4 animate-pulse"><div className="h-6 w-20 bg-muted rounded" /><div className="h-40 bg-muted rounded-xl" /><div className="h-64 bg-muted rounded-xl" /></div>
  }

  if (!session) {
    return <div className="flex flex-col items-center justify-center py-16 text-muted-foreground"><p>会话未找到</p></div>
  }

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate('/coach/sessions')}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />返回列表
      </button>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{session.scenarioName}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{session.createdAt}</span>
            {session.duration && <span>时长: {session.duration}分钟</span>}
            {session.score != null && <span className="font-bold text-foreground">得分: {session.score}</span>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />对话记录
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dialogues.map((entry, idx) => (
              <div key={idx} className={`flex gap-3 ${entry.role === 'rep' ? 'justify-end' : ''}`}>
                <div className={`max-w-[80%] rounded-lg p-3 ${
                  entry.role === 'rep' ? 'bg-blue-600 text-white' :
                  entry.role === 'system' ? 'bg-muted text-muted-foreground text-xs' :
                  'bg-background border'
                }`}>
                  {entry.role !== 'system' && (
                    <p className="text-xs font-medium mb-1">
                      {entry.role === 'rep' ? '我' : 'HCP'}
                      <span className="ml-2 opacity-60">{entry.timestamp}</span>
                    </p>
                  )}
                  <p className="text-sm">{entry.content}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
