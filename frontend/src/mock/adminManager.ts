export interface MemberPerf {
  name: string
  visits: number
  deals: number
  score: number
}

export function getMockTeamPerfData(): MemberPerf[] {
  return [
    { name: '赵建国', visits: 24, deals: 5, score: 92 },
    { name: '钱晓峰', visits: 21, deals: 3, score: 88 },
    { name: '孙丽华', visits: 18, deals: 4, score: 85 },
    { name: '李志远', visits: 16, deals: 2, score: 78 },
    { name: '周美琴', visits: 14, deals: 1, score: 75 },
  ]
}

export function getMockTeamStatusData() {
  return [
    { name: '已通过', value: 156, color: '#10b981' },
    { name: '待审核', value: 23, color: '#f59e0b' },
    { name: '已违规', value: 12, color: '#ef4444' },
  ]
}

export function getMockTeamMemberData() {
  return [
    { name: '赵建国', passed: 22, violations: 1 },
    { name: '钱晓峰', passed: 20, violations: 0 },
    { name: '孙丽华', passed: 17, violations: 1 },
    { name: '李志远', passed: 14, violations: 2 },
    { name: '周美琴', passed: 13, violations: 1 },
  ]
}

export interface Member {
  id: number
  name: string
  role: string
  visits: number
  coverage: number
  compliance: number
  status: 'active' | 'inactive'
}

export function getMockTeamMembers(): Member[] {
  return [
    { id: 1, name: '赵建国', role: '销售代表', visits: 24, coverage: 92, compliance: 96, status: 'active' },
    { id: 2, name: '钱晓峰', role: '销售代表', visits: 21, coverage: 88, compliance: 100, status: 'active' },
    { id: 3, name: '孙丽华', role: '销售代表', visits: 18, coverage: 85, compliance: 94, status: 'active' },
    { id: 4, name: '李志远', role: '销售代表', visits: 16, coverage: 78, compliance: 88, status: 'active' },
    { id: 5, name: '周美琴', role: '销售代表', visits: 14, coverage: 80, compliance: 92, status: 'active' },
    { id: 6, name: '吴国强', role: '销售代表', visits: 12, coverage: 72, compliance: 85, status: 'inactive' },
    { id: 7, name: '郑丽萍', role: '销售代表', visits: 10, coverage: 68, compliance: 90, status: 'active' },
  ]
}

export function getMockTeamStats() {
  return {
    totalVisits: 428,
    teamSize: 12,
    coverageRate: 85,
    complianceIssues: 7,
  }
}

export function getMockTeamWeeklyData() {
  return [
    { day: '周一', visits: 18 },
    { day: '周二', visits: 24 },
    { day: '周三', visits: 20 },
    { day: '周四', visits: 28 },
    { day: '周五', visits: 22 },
    { day: '周六', visits: 12 },
    { day: '周日', visits: 8 },
  ]
}
