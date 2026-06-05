export interface KpiCard {
  title: string
  value: string | number
  change: number
  icon: string
  trend: 'up' | 'down' | 'neutral'
}

export interface VisitStat {
  date: string
  count: number
  passRate: number
}

export interface TeamRank {
  name: string
  visits: number
  complianceRate: number
  deals: number
}

export interface ViolationItem {
  id: number
  repName: string
  type: string
  detail: string
  severity: 'high' | 'medium' | 'low'
  date: string
  status: 'pending' | 'resolved'
}

export interface ResearchKpi {
  title: string
  value: string | number
  change: number
  icon: string
}

export interface PiSource {
  name: string
  institution: string
  matches: number
  lastActivity: string
}

export interface ProductMatchStat {
  category: string
  total: number
  matched: number
  rate: number
}
