import client from './client'
import {
  getMockTeamStats,
  getMockTeamWeeklyData,
  getMockTeamPerfData,
  getMockTeamStatusData,
  getMockTeamMemberData,
  getMockTeamMembers,
  type MemberPerf,
  type Member,
} from '@/mock/adminManager'

export type { MemberPerf, Member }

export async function fetchManagerStats() {
  try {
    const res = await client.get('/api/admin/manager/stats')
    return res.data as {
      stats: ReturnType<typeof getMockTeamStats>
      weeklyData: ReturnType<typeof getMockTeamWeeklyData>
    }
  } catch {
    return {
      stats: getMockTeamStats(),
      weeklyData: getMockTeamWeeklyData(),
    }
  }
}

export async function fetchManagerPerformance() {
  try {
    const res = await client.get<MemberPerf[]>('/api/admin/manager/performance')
    return res.data
  } catch {
    return getMockTeamPerfData()
  }
}

export async function fetchManagerCompliance() {
  try {
    const res = await client.get('/api/admin/manager/compliance')
    return res.data as {
      statusData: ReturnType<typeof getMockTeamStatusData>
      memberData: ReturnType<typeof getMockTeamMemberData>
    }
  } catch {
    return {
      statusData: getMockTeamStatusData(),
      memberData: getMockTeamMemberData(),
    }
  }
}

export async function fetchManagerMembers() {
  try {
    const res = await client.get<Member[]>('/api/admin/manager/members')
    return res.data
  } catch {
    return getMockTeamMembers()
  }
}
