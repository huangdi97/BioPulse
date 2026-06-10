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

export function getMockExpenseWasteData() {
  return {
    summary: { totalWaste: 386000, caseCount: 24, avgRate: 16.8, trend: 'up' },
    details: [
      { id: 1, rep: '赵建国', expenseUp: 32, visitDown: 18, flowDown: 12, amount: 45000, date: '2026-05' },
      { id: 2, rep: '钱晓峰', expenseUp: 28, visitDown: 12, flowDown: 8, amount: 38000, date: '2026-05' },
      { id: 3, rep: '孙丽华', expenseUp: 22, visitDown: 15, flowDown: 5, amount: 29000, date: '2026-05' },
      { id: 4, rep: '李志远', expenseUp: 18, visitDown: 10, flowDown: 6, amount: 22000, date: '2026-04' },
      { id: 5, rep: '周美琴', expenseUp: 15, visitDown: 8, flowDown: 3, amount: 18000, date: '2026-04' },
    ],
  }
}

export function getMockVisitFraudData() {
  return {
    summary: { totalFraud: 48, caseCount: 16, detectionRate: 92, trend: 'down' },
    details: [
      { id: 1, rep: '赵建国', visitsUp: 35, flowFlat: true, score: 0.82, date: '2026-05' },
      { id: 2, rep: '孙丽华', visitsUp: 28, flowFlat: true, score: 0.78, date: '2026-05' },
      { id: 3, rep: '吴国强', visitsUp: 22, flowFlat: true, score: 0.75, date: '2026-05' },
      { id: 4, rep: '李志远', visitsUp: 18, flowFlat: true, score: 0.71, date: '2026-04' },
    ],
  }
}

export function getMockManagementNeglectData() {
  return {
    summary: { unresolvedReds: 12, avgResponseDays: 8.5, highRiskTeams: 3, trend: 'up' },
    details: [
      { id: 1, team: '西南区域', redLights: 5, unresolved: 3, managerActions: 0, risk: 'high', daysOpen: 14 },
      { id: 2, team: '西北区域', redLights: 4, unresolved: 2, managerActions: 1, risk: 'high', daysOpen: 10 },
      { id: 3, team: '华中区域', redLights: 3, unresolved: 1, managerActions: 0, risk: 'medium', daysOpen: 7 },
    ],
  }
}

export function getMockRectificationData() {
  return {
    summary: { totalIssues: 38, closed: 22, inProgress: 12, overdue: 4, closureRate: 57.9 },
    details: [
      { id: 1, issue: '费用合规违规', owner: '赵建国', status: 'closed', createdAt: '2026-05-01', closedAt: '2026-05-15', days: 14 },
      { id: 2, issue: '拜访数据不实', owner: '孙丽华', status: 'in_progress', createdAt: '2026-05-10', closedAt: '', days: 31 },
      { id: 3, issue: '礼品超限未报备', owner: '李志远', status: 'closed', createdAt: '2026-05-05', closedAt: '2026-05-12', days: 7 },
      { id: 4, issue: '话术违规未整改', owner: '钱晓峰', status: 'overdue', createdAt: '2026-04-20', closedAt: '', days: 51 },
      { id: 5, issue: '培训缺失', owner: '周美琴', status: 'in_progress', createdAt: '2026-05-20', closedAt: '', days: 21 },
    ],
  }
}

export function getMockExclusionGates() {
  return {
    gates: [
      { id: 1, name: '高价值客户豁免', rule: 'compliance.visit_fraud', enabled: true, scope: 'key_accounts', priority: 'high' },
      { id: 2, name: '新代表过渡期', rule: 'compliance.expense_waste', enabled: true, scope: 'probation_reps', priority: 'medium' },
      { id: 3, name: '紧急学术活动', rule: 'compliance.expense_approval', enabled: false, scope: 'emergency', priority: 'low' },
      { id: 4, name: '区域试点豁免', rule: 'compliance.management_neglect', enabled: true, scope: 'pilot_region', priority: 'medium' },
    ],
  }
}
