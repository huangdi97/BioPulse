export interface TeamRank {
  rank: number
  name: string
  visits: number
  compliance: number
  performance: number
  score: number
}

export function getMockTrendMonthlyData() {
  return [
    { month: '1月', revenue: 420000, target: 400000, growth: 5.0 },
    { month: '2月', revenue: 380000, target: 400000, growth: -5.0 },
    { month: '3月', revenue: 510000, target: 450000, growth: 13.3 },
    { month: '4月', revenue: 470000, target: 450000, growth: 4.4 },
    { month: '5月', revenue: 560000, target: 500000, growth: 12.0 },
    { month: '6月', revenue: 509000, target: 500000, growth: 1.8 },
  ]
}

export function getMockTeamRankings(): TeamRank[] {
  return [
    { rank: 1, name: '华东大区', visits: 245, compliance: 98, performance: 92, score: 96 },
    { rank: 2, name: '华南大区', visits: 218, compliance: 95, performance: 89, score: 92 },
    { rank: 3, name: '华北区域', visits: 196, compliance: 92, performance: 85, score: 88 },
    { rank: 4, name: '华中区域', visits: 175, compliance: 88, performance: 82, score: 84 },
    { rank: 5, name: '西南区域', visits: 152, compliance: 85, performance: 78, score: 80 },
    { rank: 6, name: '西北区域', visits: 128, compliance: 82, performance: 75, score: 76 },
    { rank: 7, name: '东北区域', visits: 110, compliance: 78, performance: 72, score: 72 },
  ]
}

export function getMockComplianceTrendData() {
  return [
    { month: '1月', violations: 12, processed: 8 },
    { month: '2月', violations: 10, processed: 7 },
    { month: '3月', violations: 15, processed: 11 },
    { month: '4月', violations: 8, processed: 6 },
    { month: '5月', violations: 6, processed: 5 },
    { month: '6月', violations: 4, processed: 4 },
  ]
}

export function getMockComplianceCategoryData() {
  return [
    { name: '话术违规', value: 35 },
    { name: '竞品提及', value: 25 },
    { name: '数据造假', value: 18 },
    { name: '礼品超限', value: 12 },
    { name: '其他', value: 10 },
  ]
}

export const PIE_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6']

export function getMockSummaryCardData() {
  return {
    totalRevenue: 2850000,
    totalVisits: 1256,
    complianceBlocks: 38,
    activeUsers: 48,
  }
}

export function getMockSummaryBarData() {
  return [
    { month: '1月', revenue: 420000, visits: 180 },
    { month: '2月', revenue: 380000, visits: 160 },
    { month: '3月', revenue: 510000, visits: 210 },
    { month: '4月', revenue: 470000, visits: 195 },
    { month: '5月', revenue: 560000, visits: 230 },
    { month: '6月', revenue: 509000, visits: 281 },
  ]
}
