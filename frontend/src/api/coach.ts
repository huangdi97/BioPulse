import client from './client'

export interface Scenario {
  id: number
  name: string
  description: string
  difficulty: 'easy' | 'medium' | 'hard'
  category: string
  duration: number
}

export interface Session {
  id: number
  scenarioId: number
  scenarioName: string
  status: 'active' | 'completed' | 'paused'
  createdAt: string
  score?: number
  duration?: number
}

export interface Assessment {
  id: number
  sessionId: number
  sessionName: string
  overallScore: number
  communicationScore: number
  productKnowledgeScore: number
  complianceScore: number
  feedback: string
  createdAt: string
}

export interface Reflection {
  id: number
  sessionId: number
  sessionName: string
  content: string
  createdAt: string
}

export async function fetchScenarios(): Promise<Scenario[]> {
  try {
    const { data } = await client.get<Scenario[]>('/api/sales-coach/scenarios')
    return data
  } catch {
    return [
      { id: 1, name: '新药处方推广', description: '向医生推广新上市药品的处方', difficulty: 'medium', category: '产品推广', duration: 30 },
      { id: 2, name: '学术会议邀约', description: '邀请HCP参加学术会议', difficulty: 'easy', category: '学术推广', duration: 15 },
      { id: 3, name: '合规异议处理', description: '应对HCP关于药品价格的异议', difficulty: 'hard', category: '异议处理', duration: 20 },
      { id: 4, name: '竞品对比拜访', description: '处理HCP对竞品的偏好', difficulty: 'hard', category: '竞争分析', duration: 25 },
    ]
  }
}

export async function fetchSessions(): Promise<Session[]> {
  try {
    const { data } = await client.get<Session[]>('/api/sales-coach/sessions')
    return data
  } catch {
    return [
      { id: 1, scenarioId: 1, scenarioName: '新药处方推广', status: 'completed', createdAt: '2026-05-28', score: 85, duration: 28 },
      { id: 2, scenarioId: 3, scenarioName: '合规异议处理', status: 'completed', createdAt: '2026-05-25', score: 72, duration: 22 },
      { id: 3, scenarioId: 2, scenarioName: '学术会议邀约', status: 'active', createdAt: '2026-05-30' },
      { id: 4, scenarioId: 4, scenarioName: '竞品对比拜访', status: 'paused', createdAt: '2026-05-29', duration: 10 },
    ]
  }
}

export async function fetchSessionDetail(id: number): Promise<Session | null> {
  try {
    const { data } = await client.get<Session>(`/api/sales-coach/sessions/${id}`)
    return data
  } catch {
    const sessions = await fetchSessions()
    return sessions.find((s) => s.id === id) ?? null
  }
}

export async function fetchAssessments(): Promise<Assessment[]> {
  try {
    const { data } = await client.get<Assessment[]>('/api/sales-coach/assessments')
    return data
  } catch {
    return [
      { id: 1, sessionId: 1, sessionName: '新药处方推广', overallScore: 85, communicationScore: 88, productKnowledgeScore: 90, complianceScore: 78, feedback: '沟通技巧出色，产品知识扎实，合规意识需加强', createdAt: '2026-05-28' },
      { id: 2, sessionId: 2, sessionName: '合规异议处理', overallScore: 72, communicationScore: 70, productKnowledgeScore: 75, complianceScore: 80, feedback: '合规处理较好，沟通可更主动', createdAt: '2026-05-25' },
    ]
  }
}

export async function fetchReflections(): Promise<Reflection[]> {
  try {
    const { data } = await client.get<Reflection[]>('/api/sales-coach/reflections')
    return data
  } catch {
    return [
      { id: 1, sessionId: 1, sessionName: '新药处方推广', content: '开场白可以更简洁，医生对新药数据反应积极，下次可以准备更多临床数据支撑', createdAt: '2026-05-28' },
      { id: 2, sessionId: 2, sessionName: '合规异议处理', content: '面对价格异议时需要保持冷静，不要急于辩解，先理解对方真实顾虑', createdAt: '2026-05-25' },
    ]
  }
}

export async function fetchCoachStats(): Promise<Record<string, unknown>> {
  try {
    const { data } = await client.get('/api/sales-coach/stats')
    return data
  } catch {
    return {
      totalSessions: 4,
      completedSessions: 2,
      averageScore: 78.5,
      totalDuration: 85,
      improvementRate: 12,
    }
  }
}
