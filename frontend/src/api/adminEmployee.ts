import client, { withFallback } from './client'
import {
  getMockEmployeeComplianceRecords,
  getMockEmployeePerf,
  getMockEmployeePerfDetails,
  getMockEmployeeProfile,
  getMockEmployeeTasks,
  getMockEmployeeTrendData,
  type ComplianceItem,
  type TaskItem,
} from '@/mock/adminEmployee'

export type { ComplianceItem, TaskItem }

export async function fetchEmployeeCompliance() {
  return withFallback(
    async () => {
      const res = await client.get<ComplianceItem[]>('/api/admin/employee/compliance')
      return res.data
    },
    () => getMockEmployeeComplianceRecords()
  )
}

export async function fetchEmployeePerformance() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/employee/performance')
      return res.data as {
        perf: ReturnType<typeof getMockEmployeePerf>
        details: ReturnType<typeof getMockEmployeePerfDetails>
      }
    },
    () => ({
      perf: getMockEmployeePerf(),
      details: getMockEmployeePerfDetails(),
    })
  )
}

export async function fetchEmployeeProfile() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/employee/profile')
      return res.data as ReturnType<typeof getMockEmployeeProfile>
    },
    () => getMockEmployeeProfile()
  )
}

export async function fetchEmployeeTasks() {
  return withFallback(
    async () => {
      const res = await client.get<TaskItem[]>('/api/admin/employee/tasks')
      return res.data
    },
    () => getMockEmployeeTasks()
  )
}

export async function fetchEmployeeTrend() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/employee/trend')
      return res.data as ReturnType<typeof getMockEmployeeTrendData>
    },
    () => getMockEmployeeTrendData()
  )
}
