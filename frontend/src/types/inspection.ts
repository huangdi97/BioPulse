export interface InspectionDashboardData {
  self_check_rate: number
  overdue_count: number
  history_records: number
  score: number
}

export interface InspectionTask {
  id: number
  title?: string
  item?: string
  description?: string
  assignee: string
  deadline: string
  status?: string
  category?: string
  remark?: string
  score?: number
  inspection_id?: string
  event?: string
  owner?: string
  date?: string
  capa_stage?: string
  result?: string
  created_at?: string
}

export interface AuditTrailItem {
  id?: number
  stage?: string
  what?: string
  who?: string
  when?: string
  evidence?: string
}

export interface TaskFormData {
  title: string
  description: string
  assignee: string
  deadline: string
}
