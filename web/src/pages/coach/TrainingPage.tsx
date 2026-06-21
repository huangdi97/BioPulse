import { useState, useMemo, useEffect } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card"
import { Input } from "../../components/ui/Input"
import { Button } from "../../components/ui/Button"
import { Badge } from "../../components/ui/Badge"
import { cn } from "../../lib/utils"
import { useAuth } from "../../auth/AuthContext"
import { getCoachModules, getCoachSessions } from "../../api/client";
import ScenarioCard from "../../components/coach/ScenarioCard"
import TrainingRecordTable from "../../components/coach/TrainingRecordTable"
import type { Scenario } from "../../types/coach"

interface ChatMessage { role: "coach" | "user"; text: string }

const coachGreetings: Record<string, string> = {
  "初访破冰":"你好！我是模拟HCP。请先做个简短的自我介绍吧。",
  "异议处理":"这款药的疗效数据我看过，和竞品比并没有明显优势。",
  "合规红线":"听说你们公司的合规政策很严，能具体说说吗？",
  "价格谈判":"你们的价格比竞品高出30%，这很难让院方接受。",
  "产品介绍":"请向我介绍这款新药的核心优势。",
  "客情维护":"小李啊，好久不见，最近你们公司有什么新动态？",
  "科室会演讲":"各位老师好，今天我们重点讨论一下这款药的临床价值。",
  "竞品对比":"我看过你们和A公司的对比数据，差异并不显著。",
}

const coachReplies = [
  "嗯，说得不错，能再具体一点吗？","这个观点我认同，但还有没有其他角度？",
  "让我想想…你的逻辑挺清晰的。","如果从循证医学的角度看呢？",
  "你提到的是临床获益，那安全性数据呢？","好的，换个思路——假如院长坚持降价呢？",
  "这个回复很专业，继续保持。","我理解你的意思，但证据来源可靠吗？",
  "你沟通的方式很自然，患者也能听懂。",
]

// ── Difficulty/category mapping from backend values ──
const DIFFICULTY_MAP: Record<string, "初级" | "中级" | "高级"> = {
  beginner: "初级",
  medium: "中级",
  advanced: "高级",
  expert: "高级",
}

const CATEGORY_MAP: Record<string, string> = {
  compliance: "合规",
  visit: "拜访",
  objection: "异议",
  negotiation: "谈判",
  product_intro: "产品介绍",
  presentation: "产品介绍",
  communication: "拜访",
  skill: "拜访",
  // fallback: keep original
}

function mapModuleToScenario(mod: any, completedMap: Set<number>, scoreMap: Map<number, number>): Scenario {
  const diff = DIFFICULTY_MAP[mod.difficulty] || "中级"
  const cat = CATEGORY_MAP[mod.category] || mod.category || "拜访"
  const id = mod.id
  const completed = completedMap.has(id)
  const score = scoreMap.get(id) || 0
  return {
    id,
    name: mod.title,
    description: mod.content || mod.description || "",
    difficulty: diff,
    category: cat as Scenario["category"],
    completed,
    score,
    duration: mod.estimated_minutes || 15,
    tags: [cat, diff],
  }
}

function KpiCard({ title, value, accent }: { title: string; value: string; accent: string }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent><p className="text-3xl font-bold" style={{ color: accent }}>{value}</p></CardContent>
    </Card>
  )
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-2 rounded-full" style={{ backgroundColor: "var(--clr-gray-20)" }}>
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${value}%`, backgroundColor: color }} />
    </div>
  )
}

function ScoreSidebar({ scores }: { scores: { label: string; value: number; color: string }[] }) {
  const total = Math.round(scores.reduce((s, m) => s + m.value, 0) / scores.length)
  return (
    <Card>
      <CardHeader><CardTitle>实时评分</CardTitle></CardHeader>
      <CardContent className="space-y-5">
        {scores.map(m => (
          <div key={m.label} className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span style={{ color: "var(--clr-text-primary)" }}>{m.label}</span>
              <span className="font-semibold" style={{ color: m.color }}>{m.value}</span>
            </div>
            <ProgressBar value={m.value} color={m.color} />
          </div>
        ))}
        <div className="pt-3 border-t" style={{ borderColor: "var(--clr-gray-20)" }}>
          <div className="flex items-center justify-between text-sm">
            <span style={{ color: "var(--clr-text-secondary)" }}>综合得分</span>
            <span className="text-xl font-bold" style={{ color: "var(--clr-brand)" }}>{total}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ChatPanel({ scenario, messages, onSend }: {
  scenario: Scenario | null; messages: ChatMessage[]; onSend: (text: string) => void
}) {
  const [input, setInput] = useState("")
  const handleSend = () => { const t = input.trim(); if (!t) return; onSend(t); setInput("") }
  return (
    <Card className="flex flex-col" style={{ minHeight: 380 }}>
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-sm">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold"
            style={{ backgroundColor: "var(--clr-brand)", color: "var(--clr-text-inverse)" }}>AI</span>
          <span style={{ color: "var(--clr-text-primary)" }}>{scenario ? `模拟对练 · ${scenario.name}` : "模拟对练"}</span>
          {scenario && <Badge variant="default" className="ml-auto">{scenario.difficulty}</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col flex-1 gap-0 pt-3">
        <div className="flex-1 space-y-3 overflow-y-auto mb-3 p-2 rounded-md"
          style={{ minHeight: 200, maxHeight: 320, backgroundColor: "var(--clr-gray-10)" }}>
          {messages.length === 0 && !scenario && (
            <p className="text-sm text-center pt-10" style={{ color: "var(--clr-text-placeholder)" }}>请选择一个场景开始训练</p>
          )}
          {messages.length === 0 && scenario && (
            <div className="flex items-start gap-2">
              <span className="shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-full text-[10px] font-bold"
                style={{ backgroundColor: "var(--clr-brand)", color: "var(--clr-text-inverse)" }}>AI</span>
              <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm"
                style={{ backgroundColor: "var(--clr-surface-card)", color: "var(--clr-text-primary)", boxShadow: "var(--shadow-border)" }}>
                {coachGreetings[scenario.name] ?? "开始训练吧。"}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={cn("flex items-start gap-2", msg.role === "user" && "flex-row-reverse")}>
              <span className={cn("shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-full text-[10px] font-bold",
                msg.role === "coach" ? "bg-[var(--clr-brand)] text-[var(--clr-text-inverse)]" : "bg-[var(--clr-gray-50)] text-[var(--clr-text-inverse)]"
              )}>{msg.role === "coach" ? "AI" : "我"}</span>
              <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm"
                style={{ backgroundColor: msg.role === "coach" ? "var(--clr-surface-card)" : "var(--clr-brand)", color: msg.role === "coach" ? "var(--clr-text-primary)" : "var(--clr-text-inverse)", boxShadow: msg.role === "coach" ? "var(--shadow-border)" : "none" }}>
                {msg.text}
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Input placeholder={scenario ? "输入你的回答..." : "请先选择一个场景"} value={input}
            onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSend()} disabled={!scenario} />
          <Button size="sm" onClick={handleSend} disabled={!scenario || !input.trim()}>发送</Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function TrainingPage() {
  const { user } = useAuth()
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [showScore, setShowScore] = useState(false)

  // Real backend data
  const [modules, setModules] = useState<any[]>([])
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const [mods, sessData] = await Promise.all([
          getCoachModules(),
          getCoachSessions(user?.id),
        ])
        setModules(mods || [])
        setSessions(sessData?.items || [])
      } catch {
        // leave empty
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [user?.id])

  // Build completed map and score map from sessions
  const { completedMap, scoreMap } = useMemo(() => {
    const cm = new Set<number>()
    const sm = new Map<number, number>()
    for (const s of sessions) {
      const mid = s.module_id
      if (s.passed) cm.add(mid)
      const existing = sm.get(mid) || 0
      if (s.score > existing) sm.set(mid, Math.round(s.score * 100))
    }
    return { completedMap: cm, scoreMap: sm }
  }, [sessions])

  const allScenarios = useMemo(() =>
    modules.map(m => mapModuleToScenario(m, completedMap, scoreMap)),
    [modules, completedMap, scoreMap]
  )

  const trainingRecords = useMemo(() =>
    sessions.map((s: any) => {
      const mod = modules.find((m: any) => m.id === s.module_id)
      return {
        id: s.id,
        scenario_name: mod?.title || `模块 #${s.module_id}`,
        date: (s.completed_at || s.created_at || "").slice(0, 10),
        score: Math.round((s.score || 0) * 100),
        duration: Math.round((s.time_spent_seconds || 0) / 60),
        weakness: s.feedback || "",
        strength: "",
      }
    }),
    [sessions, modules]
  )

  const totalTrainings = sessions.length
  const avgScore = trainingRecords.length
    ? Math.round(trainingRecords.reduce((s, r) => s + r.score, 0) / trainingRecords.length)
    : 0
  const pendingCount = modules.length - completedMap.size

  const scores = useMemo(() => {
    const count = messages.length
    return [
      { label: "话术分", value: Math.min(count * 12 + 10, 95), color: "var(--clr-brand)" },
      { label: "合规分", value: Math.min(count * 10 + 20, 92), color: "var(--clr-mode-pass)" },
      { label: "技巧分", value: Math.min(count * 8 + 15, 88), color: "var(--clr-mode-warn)" },
    ]
  }, [messages.length])

  const handleSelectScenario = (s: Scenario) => { setSelectedScenario(s); setMessages([]) }
  const handleSend = (text: string) => {
    if (!selectedScenario) return
    setMessages(prev => [...prev, { role: "user", text }, { role: "coach", text: coachReplies[Math.floor(Math.random() * coachReplies.length)] }])
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: "var(--clr-text-primary)" }}>销售教练</h1>
        <p className="text-sm mt-0.5" style={{ color: "var(--clr-text-secondary)" }}>情景模拟训练与能力评估</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="总训练次数" value={String(totalTrainings)} accent="var(--clr-brand)" />
        <KpiCard title="平均分" value={`${avgScore}`} accent="var(--clr-mode-pass)" />
        <KpiCard title="待练习场景" value={String(pendingCount)} accent="var(--clr-mode-warn)" />
      </div>

      {loading ? (
        <div className="text-center py-8 text-sm" style={{ color: "var(--clr-text-secondary)" }}>加载中...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader><CardTitle>场景选择器</CardTitle></CardHeader>
              <CardContent>
                {allScenarios.length === 0 ? (
                  <p className="text-sm text-center py-4" style={{ color: "var(--clr-text-secondary)" }}>暂无可用训练模块</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {allScenarios.map(s => (
                      <button key={s.id} onClick={() => handleSelectScenario(s)}
                        className={cn("relative rounded-[var(--radius-lg)] border-2 p-0 text-left transition-all",
                          selectedScenario?.id === s.id ? "border-[var(--clr-brand)]" : "border-transparent hover:border-[var(--clr-gray-30)]"
                        )}>
                        <ScenarioCard scenario={s} />
                        {selectedScenario?.id === s.id && (
                          <span className="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                            style={{ backgroundColor: "var(--clr-brand)", color: "var(--clr-text-inverse)" }}>✓</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            <ChatPanel scenario={selectedScenario} messages={messages} onSend={handleSend} />
          </div>
          <div className="space-y-4">
            <button
              className="flex md:hidden items-center justify-between w-full p-3 rounded-lg border text-sm"
              style={{ borderColor: 'var(--clr-border-default)', color: 'var(--clr-text-primary)' }}
              onClick={() => setShowScore(!showScore)}
            >
              实时评分
              <ChevronDown className={cn("w-4 h-4 transition-transform", showScore && "rotate-180")} />
            </button>
            <div className={cn(showScore ? "block" : "hidden", "md:block")}>
              <ScoreSidebar scores={scores} />
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>训练历史</CardTitle></CardHeader>
        <CardContent>
          {trainingRecords.length === 0 ? (
            <p className="text-sm text-center py-4" style={{ color: "var(--clr-text-secondary)" }}>暂无训练记录</p>
          ) : (
            <TrainingRecordTable records={trainingRecords} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
