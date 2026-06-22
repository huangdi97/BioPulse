export interface User {
  username: string
  role?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface HCP {
  id: number
  name: string
  hospital: string
  dept: string
  region: string
  title: string
  priority: 'high' | 'medium' | 'low'
  lastVisit: string
  avatar?: string
}

export interface Task {
  id: number
  title: string
  description?: string
  status: 'pending' | 'completed'
  dueDate?: string
  relatedHcpId?: number
}

export interface DashboardSummary {
  pendingTasks: number
  todayVisits: number
  complianceAlerts: number
}

export interface Violation {
  keyword: string
  category: string
  riskLevel: string
  suggestion?: string
}

export interface ScanResult {
  passed: boolean
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  violations: Violation[]
  score: number
}

export interface VisitRecord {
  id: number
  hcpId: number
  hcpName: string
  content: string
  visitType: string
  createdAt: string
  complianceStatus: 'passed' | 'violated' | 'pending'
  evidence_photos?: string[]
  location?: string
  location_mode?: string
  violations?: Violation[]
  date?: string
  summary?: string
}

export interface AiSuggestion {
  id: number
  title: string
  content: string
  type: 'visit_priority' | 'follow_up' | 'insight' | 'compliance_tip'
  relatedHcpName?: string
  createdAt: string
}

export interface TeamSummary {
  totalVisits: number
  teamSize: number
  coverageRate: number
  complianceIssues: number
  visitsTrend: 'up' | 'down'
  visitsTrendValue: string
}

export interface TeamMember {
  id: number
  name: string
  visitCount: number
  coverage: number
  complianceRate: number
  opportunityCount: number
}

export type OpportunityStage = 'lead' | 'follow_up' | 'negotiation' | 'closed_won'

export interface Opportunity {
  id: number
  title: string
  hospital: string
  amount: string
  stage: OpportunityStage
  owner: string
  probability: number
  expectedClose: string
}

export interface ComplianceRecord {
  id: number
  repName: string
  repId: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  category: string
  keyword: string
  content: string
  suggestion: string
  status: 'pending' | 'reviewed' | 'dismissed'
  createdAt: string
  reviewedAt?: string
}

export interface ComplianceDashboard {
  todayViolations: number
  weeklyTotal: number
  processedRate: number
  highRiskCount: number
  dailyTrend: { date: string; count: number }[]
  topCategories: { category: string; count: number; percentage: number }[]
  topReps: { repName: string; violationCount: number; riskLevel: string }[]
}

export interface AuditEntry {
  timestamp: string
  action: string
  actor: string
  verified: boolean
}

export interface ApprovalRecord {
  id: number
  quotation_id: string
  rep_name: string
  product: string
  amount: number
  limit_amount: number
  status: string
  review_notes?: string
  created_at: string
}

export interface AdmissionRecord {
  id: number
  hospital_name: string
  department: string
  product: string
  status: string
  meeting_date: string | null
  notes: string
  rep_name: string
  created_at: string
}

export interface RecommendationItem {
  id: number
  title: string
  content: string
  type: 'follow_up' | 'competitor_alert' | 'compliance_tip'
}

export interface VisitReasonItem {
  hcp_name: string
  reason: string
  material: string
}

export interface ExpenseAlertItem {
  expense_id: number
  alert: string
  severity: 'low' | 'medium' | 'high'
}

export interface TodayRecommendation {
  recommendations: RecommendationItem[]
  visit_reasons: VisitReasonItem[]
  expense_alerts: ExpenseAlertItem[]
}
