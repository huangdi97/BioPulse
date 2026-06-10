import client, { withFallback } from './client'

export interface OppRecord {
  id: number
  title: string
  hospital: string
  amount: string
  stage: 'lead' | 'follow_up' | 'negotiation' | 'closed_won'
  owner: string
  probability: number
  expectedClose: string
  createdAt: string
}

export interface Bidding {
  id: number
  opportunityId: number
  title: string
  status: 'preparing' | 'submitted' | 'won' | 'lost'
  deadline: string
  amount: string
  createdAt: string
}

export interface Contact {
  id: number
  name: string
  title: string
  hospital: string
  department: string
  phone: string
  email: string
  role: string
}

export interface TrendData {
  month: string
  revenue: number
  opportunities: number
  winRate: number
}

export async function fetchOpportunities(): Promise<OppRecord[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<OppRecord[]>('/api/opportunity/opportunities')
      return data
    },
    () => [
      { id: 1, title: '新药进院项目', hospital: '北京协和医院', amount: '¥500,000', stage: 'negotiation' as const, owner: '张三', probability: 75, expectedClose: '2026-06-30', createdAt: '2026-05-01' },
      { id: 2, title: '学术会议合作', hospital: '上海瑞金医院', amount: '¥300,000', stage: 'follow_up' as const, owner: '李四', probability: 50, expectedClose: '2026-07-15', createdAt: '2026-05-10' },
      { id: 3, title: '临床研究赞助', hospital: '广州中山医院', amount: '¥800,000', stage: 'lead' as const, owner: '王五', probability: 30, expectedClose: '2026-08-01', createdAt: '2026-05-20' },
      { id: 4, title: '药品采购合同', hospital: '杭州第一人民医院', amount: '¥200,000', stage: 'closed_won' as const, owner: '赵六', probability: 100, expectedClose: '2026-05-25', createdAt: '2026-04-15' },
    ]
  )
}

export async function fetchOpportunityDetail(id: number): Promise<OppRecord | null> {
  return withFallback(
    async () => {
      const { data } = await client.get<OppRecord>(`/api/opportunity/opportunities/${id}`)
      return data
    },
    async () => {
      const list = await fetchOpportunities()
      return list.find((o) => o.id === id) ?? null
    }
  )
}

export async function fetchBiddings(): Promise<Bidding[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<Bidding[]>('/api/opportunity/bidding')
      return data
    },
    () => [
      { id: 1, opportunityId: 1, title: '新药进院投标', status: 'preparing' as const, deadline: '2026-06-15', amount: '¥500,000', createdAt: '2026-05-01' },
      { id: 2, opportunityId: 3, title: '临床研究设备采购', status: 'submitted' as const, deadline: '2026-06-30', amount: '¥800,000', createdAt: '2026-05-15' },
    ]
  )
}

export async function fetchContacts(): Promise<Contact[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<Contact[]>('/api/opportunity/contacts')
      return data
    },
    () => [
      { id: 1, name: '张主任', title: '心内科主任', hospital: '北京协和医院', department: '心内科', phone: '13800001111', email: 'zhang@hospital.cn', role: '决策者' },
      { id: 2, name: '李药师', title: '药学部主任', hospital: '上海瑞金医院', department: '药学部', phone: '13900002222', email: 'li@hospital.cn', role: '影响者' },
    ]
  )
}

export async function fetchTrends(): Promise<TrendData[]> {
  return withFallback(
    async () => {
      const { data } = await client.get<TrendData[]>('/api/opportunity/trends')
      return data
    },
    () => [
      { month: '2026-01', revenue: 120, opportunities: 8, winRate: 40 },
      { month: '2026-02', revenue: 150, opportunities: 10, winRate: 45 },
      { month: '2026-03', revenue: 180, opportunities: 12, winRate: 50 },
      { month: '2026-04', revenue: 220, opportunities: 14, winRate: 52 },
      { month: '2026-05', revenue: 250, opportunities: 16, winRate: 55 },
    ]
  )
}

export async function fetchOppStats(): Promise<Record<string, unknown>> {
  return withFallback(
    async () => {
      const { data } = await client.get('/api/opportunity/stats')
      return data
    },
    () => ({ total: 4, active: 3, totalAmount: '¥1,800,000', avgProbability: 64, winRate: 25 })
  )
}
