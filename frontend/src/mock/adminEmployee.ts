export interface ComplianceItem {
  id: number
  date: string
  type: string
  result: 'passed' | 'violated' | 'pending'
  detail: string
}

export const resultColors: Record<string, string> = {
  passed: 'bg-green-50 text-green-700 border-green-200',
  violated: 'bg-red-50 text-red-700 border-red-200',
  pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
}

export const resultLabels: Record<string, string> = {
  passed: '已通过',
  violated: '已违规',
  pending: '待审核',
}

export function getMockEmployeeComplianceRecords(): ComplianceItem[] {
  return [
    { id: 1, date: '2026-05-28', type: '拜访合规检查', result: 'passed', detail: '5月28日拜访华东医院合规检查通过' },
    { id: 2, date: '2026-05-25', type: '话术合规扫描', result: 'passed', detail: '话术内容合规，无违规关键词' },
    { id: 3, date: '2026-05-20', type: '数据真实性核查', result: 'violated', detail: '拜访记录中存在数据不一致情况，需修正' },
    { id: 4, date: '2026-05-15', type: '礼品合规检查', result: 'passed', detail: '礼品登记信息完整，无超限情况' },
    { id: 5, date: '2026-05-10', type: '合规培训', result: 'pending', detail: '待完成合规培训课程' },
  ]
}

export interface TaskItem {
  id: number
  title: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'completed'
}

export const priorityColors: Record<string, string> = {
  high: 'bg-red-50 text-red-700 border-red-200',
  medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  low: 'bg-blue-50 text-blue-700 border-blue-200',
}

export const priorityLabels: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

export const statusLabels: Record<string, string> = {
  pending: '待处理',
  completed: '已完成',
}

export function getMockEmployeeTasks(): TaskItem[] {
  return [
    { id: 1, title: '拜访华东医院张主任', dueDate: '2026-06-05', priority: 'high', status: 'pending' },
    { id: 2, title: '提交5月拜访报告', dueDate: '2026-06-02', priority: 'high', status: 'completed' },
    { id: 3, title: '合规培训课程学习', dueDate: '2026-06-10', priority: 'medium', status: 'pending' },
    { id: 4, title: '更新客户信息表', dueDate: '2026-06-07', priority: 'low', status: 'pending' },
    { id: 5, title: '准备产品演示材料', dueDate: '2026-06-03', priority: 'medium', status: 'completed' },
    { id: 6, title: '参加区域销售会议', dueDate: '2026-06-08', priority: 'high', status: 'pending' },
  ]
}

export function getMockEmployeeProfile() {
  return {
    name: '张小明',
    email: 'zhangxm@example.com',
    dept: '销售部',
    joinDate: '2024-03-15',
    role: '高级销售代表',
    region: '华东区域',
  }
}

export function getMockEmployeeTrendData() {
  return [
    { month: '1月', visits: 18, revenue: 140000, score: 82 },
    { month: '2月', visits: 15, revenue: 125000, score: 78 },
    { month: '3月', visits: 20, revenue: 168000, score: 85 },
    { month: '4月', visits: 22, revenue: 175000, score: 86 },
    { month: '5月', visits: 25, revenue: 192000, score: 88 },
    { month: '6月', visits: 22, revenue: 185000, score: 88 },
  ]
}

export function getMockEmployeePerf() {
  return {
    monthlyVisits: 22,
    monthlyRevenue: 185000,
    growth: 15,
    score: 88,
    rank: 'A',
  }
}

export function getMockEmployeePerfDetails() {
  return [
    { label: '拜访完成率', value: '92%', color: 'text-green-600' },
    { label: '合规通过率', value: '96%', color: 'text-green-600' },
    { label: '客户转化率', value: '23%', color: 'text-blue-600' },
    { label: '任务完成率', value: '85%', color: 'text-yellow-600' },
  ]
}
