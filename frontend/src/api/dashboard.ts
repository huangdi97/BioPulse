import client from './client'
import type { DashboardSummary } from '@/types'

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  try {
    const response = await client.get<DashboardSummary>(
      '/api/cloud/dashboard/team/summary'
    )
    return response.data
  } catch {
    return {
      pendingTasks: 3,
      todayVisits: 5,
      complianceAlerts: 1,
    }
  }
}
