import client, { withFallback } from './client'

export interface AssistantHcp {
  id: number
  name: string
  title: string
  hospital: string
  dept: string
  region: string
  priority: string
}

export interface VisitRecord {
  id: number
  hcpId: number
  hcpName: string
  visitType: string
  summary: string
  date: string
  complianceStatus: string
}

export interface AssistantTask {
  id: number
  title: string
  description: string
  status: string
  dueDate: string
  priority: string
}

export interface KnowledgeItem {
  id: number
  title: string
  category: string
  summary: string
  updatedAt: string
}

export async function fetchAssistantHcps(): Promise<AssistantHcp[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<AssistantHcp[]>('/api/assistant/hcps')
      return data
    },
    () => [
      { id: 1, name: '张主任', title: '心内科主任', hospital: '北京协和医院', dept: '心内科', region: '北京', priority: 'high' },
      { id: 2, name: '李药师', title: '药学部主任', hospital: '上海瑞金医院', dept: '药学部', region: '上海', priority: 'medium' },
      { id: 3, name: '王教授', title: '肿瘤科主任', hospital: '广州中山医院', dept: '肿瘤科', region: '广州', priority: 'high' },
    ]
  )
}

export async function fetchAssistantHcpDetail(id: number): Promise<AssistantHcp | null> {
  return withFallback(
    async () => {
      const { data } = await client.get<AssistantHcp>(`/api/assistant/hcps/${id}`)
      return data
    },
    async () => {
      const list = await fetchAssistantHcps()
      return list.find((h) => h.id === id) ?? null
    }
  )
}

export async function fetchVisits(): Promise<VisitRecord[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<VisitRecord[]>('/api/assistant/visits')
      return data
    },
    () => [
      { id: 1, hcpId: 1, hcpName: '张主任', visitType: '实地拜访', summary: '新产品介绍和处方讨论', date: '2026-05-28', complianceStatus: 'passed' },
      { id: 2, hcpId: 2, hcpName: '李药师', visitType: '线上会议', summary: '学术文献分享', date: '2026-05-25', complianceStatus: 'passed' },
    ]
  )
}

export async function fetchAssistantTasks(): Promise<AssistantTask[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<AssistantTask[]>('/api/assistant/tasks')
      return data
    },
    () => [
      { id: 1, title: '拜访张主任', description: '讨论新药处方方案', status: 'pending', dueDate: '2026-06-02', priority: 'high' },
      { id: 2, title: '准备学术资料', description: '整理临床研究数据', status: 'completed', dueDate: '2026-05-30', priority: 'medium' },
    ]
  )
}

export async function fetchKnowledge(): Promise<KnowledgeItem[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<KnowledgeItem[]>('/api/assistant/knowledge')
      return data
    },
    () => [
      { id: 1, title: '新产品临床指南', category: '产品知识', summary: '涵盖适应症、用法用量、禁忌症等内容', updatedAt: '2026-05-20' },
      { id: 2, title: '竞品对比分析', category: '竞争情报', summary: '主要竞品的优劣势对比', updatedAt: '2026-05-15' },
      { id: 3, title: '合规推广规范', category: '合规', summary: '学术推广活动合规要点', updatedAt: '2026-05-10' },
    ]
  )
}

export async function postQA(question: string): Promise<{ answer: string }> {
  return withFallback(
    async () => {
      const { data } = await client.post<{ answer: string }>('/api/assistant/qa', { question })
      return data
    },
    () => ({ answer: `关于"${question}"的回答：这是一个很好的问题。根据最新的指南和临床数据，建议结合患者具体情况综合判断。` })
  )
}
