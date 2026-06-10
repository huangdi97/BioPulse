import client, { withFallback } from './client'
import type { DashboardSummary } from '@/types'

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return withFallback(
    async () => {
      const response = await client.get<DashboardSummary>('/api/cloud/dashboard/team/summary')
      return response.data
    },
    () => ({
      pendingTasks: 3,
      todayVisits: 5,
      complianceAlerts: 1,
    })
  )
}
