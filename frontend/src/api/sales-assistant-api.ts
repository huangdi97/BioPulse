import client from './client'

export interface PreCallInfo {
  hcpName: string
  hospital: string
  dept: string
  lastVisit: string
  suggestions: string[]
  keyPoints: string[]
}

export interface ContentItem {
  id: number
  title: string
  type: string
  category: string
  summary: string
  updatedAt: string
}

export interface StrategyAdvice {
  id: number
  title: string
  target: string
  approach: string
  expectedOutcome: string
  confidence: number
}

export interface ObjectionItem {
  id: number
  objection: string
  response: string
  category: string
  effectiveness: number
}

export interface NoteItem {
  id: number
  title: string
  content: string
  relatedTo: string
  createdAt: string
}

export interface FunnelStage {
  stage: string
  count: number
  amount: string
}

export interface ScheduleItem {
  id: number
  title: string
  time: string
  location: string
  relatedHcp: string
  status: string
}

export async function fetchPreCall(): Promise<PreCallInfo> {
  try {
    const { data } = await client.get<PreCallInfo>('/api/sales-assistant/precall')
    return data
  } catch {
    return {
      hcpName: '张主任',
      hospital: '北京协和医院',
      dept: '心内科',
      lastVisit: '2026-05-20',
      suggestions: ['准备最新临床研究数据', '回顾上次会议讨论要点', '准备竞品对比分析'],
      keyPoints: ['新药优势数据', '成本效益分析', '患者案例分享'],
    }
  }
}

export async function fetchContent(): Promise<ContentItem[]> {
  try {
    const { data } = await client.get<ContentItem[]>('/api/sales-assistant/content')
    return data
  } catch {
    return [
      { id: 1, title: '产品介绍PPT', type: 'presentation', category: '产品推广', summary: '新药产品核心卖点和临床数据', updatedAt: '2026-05-15' },
      { id: 2, title: '学术文献汇编', type: 'document', category: '学术推广', summary: '最新发表的相关研究文献', updatedAt: '2026-05-10' },
      { id: 3, title: '患者教育手册', type: 'brochure', category: '患者教育', summary: '面向患者的疾病知识手册', updatedAt: '2026-05-05' },
    ]
  }
}

export async function fetchStrategy(): Promise<StrategyAdvice[]> {
  try {
    const { data } = await client.get<StrategyAdvice[]>('/api/sales-assistant/strategy')
    return data
  } catch {
    return [
      { id: 1, title: '学术导向策略', target: '心内科主任', approach: '以最新临床试验数据为切入点', expectedOutcome: '获得处方意向', confidence: 85 },
      { id: 2, title: '患者获益策略', target: '内分泌科', approach: '强调患者生活质量改善', expectedOutcome: '增加处方量', confidence: 72 },
    ]
  }
}

export async function fetchObjections(): Promise<ObjectionItem[]> {
  try {
    const { data } = await client.get<ObjectionItem[]>('/api/sales-assistant/objections')
    return data
  } catch {
    return [
      { id: 1, objection: '价格太高', response: '从长期来看，成本效益优于竞品，可降低总治疗费用', category: '价格', effectiveness: 80 },
      { id: 2, objection: '安全性担忧', response: '三期临床数据显示安全性良好，不良事件发生率低于行业标准', category: '安全', effectiveness: 90 },
      { id: 3, objection: '已习惯现有方案', response: '新方案在关键指标上有显著优势，可逐步过渡', category: '习惯', effectiveness: 65 },
    ]
  }
}

export async function fetchNotes(): Promise<NoteItem[]> {
  try {
    const { data } = await client.get<NoteItem[]>('/api/sales-assistant/notes')
    return data
  } catch {
    return [
      { id: 1, title: '张主任拜访笔记', content: '对数据很感兴趣，希望看到更多真实世界证据', relatedTo: '张主任', createdAt: '2026-05-28' },
      { id: 2, title: '学术会议准备', content: '需要3份产品资料，要准备20分钟的演讲', relatedTo: '学术会议', createdAt: '2026-05-25' },
    ]
  }
}

export async function fetchFunnel(): Promise<FunnelStage[]> {
  try {
    const { data } = await client.get<FunnelStage[]>('/api/sales-assistant/funnel')
    return data
  } catch {
    return [
      { stage: '潜在客户', count: 25, amount: '¥1,200,000' },
      { stage: '初次接触', count: 15, amount: '¥800,000' },
      { stage: '需求确认', count: 8, amount: '¥500,000' },
      { stage: '方案呈现', count: 5, amount: '¥350,000' },
      { stage: '关闭赢单', count: 3, amount: '¥200,000' },
    ]
  }
}

export async function fetchSchedule(): Promise<ScheduleItem[]> {
  try {
    const { data } = await client.get<ScheduleItem[]>('/api/sales-assistant/schedule')
    return data
  } catch {
    return [
      { id: 1, title: '拜访张主任', time: '2026-06-02 09:00', location: '北京协和医院', relatedHcp: '张主任', status: 'scheduled' },
      { id: 2, title: '团队周会', time: '2026-06-03 14:00', location: '公司会议室', relatedHcp: '-', status: 'scheduled' },
      { id: 3, title: '学术会议', time: '2026-06-05 08:00', location: '国际会议中心', relatedHcp: '多位', status: 'preparing' },
    ]
  }
}
