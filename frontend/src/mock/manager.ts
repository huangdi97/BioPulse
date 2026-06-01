import type { TeamSummary, TeamMember, Opportunity } from '@/types'

export const mockTeamSummary: TeamSummary = {
  totalVisits: 128,
  teamSize: 12,
  coverageRate: 85,
  complianceIssues: 3,
  visitsTrend: 'up',
  visitsTrendValue: '较上月+12%',
}

export const mockTeamRanking: TeamMember[] = [
  { id: 101, name: '赵建国', visitCount: 24, coverage: 92, complianceRate: 96, opportunityCount: 5 },
  { id: 102, name: '钱晓峰', visitCount: 21, coverage: 88, complianceRate: 100, opportunityCount: 3 },
  { id: 103, name: '孙丽华', visitCount: 18, coverage: 85, complianceRate: 94, opportunityCount: 4 },
  { id: 104, name: '李志远', visitCount: 16, coverage: 78, complianceRate: 88, opportunityCount: 2 },
  { id: 105, name: '周美琴', visitCount: 14, coverage: 80, complianceRate: 92, opportunityCount: 1 },
]

export const mockOpportunities: Opportunity[] = [
  {
    id: 201,
    title: '瑞达新药进院',
    hospital: '北京协和医院',
    amount: '¥580,000',
    stage: 'negotiation',
    owner: '赵建国',
    probability: 65,
    expectedClose: '2026-07-15',
  },
  {
    id: 202,
    title: '注射用瑞舒康招标',
    hospital: '复旦大学附属中山医院',
    amount: '¥1,200,000',
    stage: 'lead',
    owner: '钱晓峰',
    probability: 20,
    expectedClose: '2026-09-01',
  },
  {
    id: 203,
    title: '口服降糖药学术推广',
    hospital: '中山大学附属第一医院',
    amount: '¥320,000',
    stage: 'follow_up',
    owner: '孙丽华',
    probability: 45,
    expectedClose: '2026-08-20',
  },
  {
    id: 204,
    title: '消化产品线准入',
    hospital: '上海瑞金医院',
    amount: '¥890,000',
    stage: 'closed_won',
    owner: '赵建国',
    probability: 100,
    expectedClose: '2026-05-28',
  },
  {
    id: 205,
    title: '神经内科新药推荐',
    hospital: '浙江大学医学院附属第一医院',
    amount: '¥450,000',
    stage: 'lead',
    owner: '李志远',
    probability: 15,
    expectedClose: '2026-10-10',
  },
  {
    id: 206,
    title: '呼吸科药品续约',
    hospital: '北京协和医院',
    amount: '¥670,000',
    stage: 'follow_up',
    owner: '周美琴',
    probability: 40,
    expectedClose: '2026-07-30',
  },
]
