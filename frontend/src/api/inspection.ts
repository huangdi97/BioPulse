import client, { getApiUrl } from '@/api/client'
import type { InspectionDashboardData, InspectionTask, AuditTrailItem, TaskFormData } from '@/types/inspection'

export async function fetchDashboard(): Promise<InspectionDashboardData> {
  const res = await client.get(getApiUrl('cloud', '/api/inspection/dashboard'))
  return res.data as InspectionDashboardData
}

export async function fetchChecklist(category?: string): Promise<InspectionTask[]> {
  const params = category && category !== '全部' ? `?category=${category}` : ''
  const res = await client.get(getApiUrl('cloud', `/api/inspection/checklist${params}`))
  return (res.data as InspectionTask[]) || []
}

export async function fetchHistory(): Promise<InspectionTask[]> {
  const res = await client.get(getApiUrl('cloud', '/api/inspection/history'))
  return (res.data as InspectionTask[]) || []
}

export async function createTask(data: TaskFormData): Promise<InspectionTask> {
  const res = await client.post(getApiUrl('cloud', '/api/inspection/task'), data)
  return res.data as InspectionTask
}

export async function confirmTask(taskId: string, evidence: string): Promise<unknown> {
  const res = await client.put(getApiUrl('cloud', `/api/inspection/task/${taskId}/confirm`), { evidence })
  return res.data
}

export async function fetchAuditTrail(inspectionId: string): Promise<AuditTrailItem[]> {
  const res = await client.get(getApiUrl('cloud', `/api/inspection/${inspectionId}/audit-trail`))
  const data = res.data as Record<string, unknown>
  return (data?.trail as AuditTrailItem[]) || (data as AuditTrailItem[]) || []
}
