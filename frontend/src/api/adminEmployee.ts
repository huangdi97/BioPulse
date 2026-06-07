import client from './client'
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
  try {
    const res = await client.get<ComplianceItem[]>('/api/admin/employee/compliance')
    return res.data
  } catch {
    return getMockEmployeeComplianceRecords()
  }
}

export async function fetchEmployeePerformance() {
  try {
    const res = await client.get('/api/admin/employee/performance')
    return res.data as {
      perf: ReturnType<typeof getMockEmployeePerf>
      details: ReturnType<typeof getMockEmployeePerfDetails>
    }
  } catch {
    return {
      perf: getMockEmployeePerf(),
      details: getMockEmployeePerfDetails(),
    }
  }
}

export async function fetchEmployeeProfile() {
  try {
    const res = await client.get('/api/admin/employee/profile')
    return res.data as ReturnType<typeof getMockEmployeeProfile>
  } catch {
    return getMockEmployeeProfile()
  }
}

export async function fetchEmployeeTasks() {
  try {
    const res = await client.get<TaskItem[]>('/api/admin/employee/tasks')
    return res.data
  } catch {
    return getMockEmployeeTasks()
  }
}

export async function fetchEmployeeTrend() {
  try {
    const res = await client.get('/api/admin/employee/trend')
    return res.data as ReturnType<typeof getMockEmployeeTrendData>
  } catch {
    return getMockEmployeeTrendData()
  }
}
