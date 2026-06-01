import client from './client'
import type { TeamSummary, TeamMember, Opportunity } from '@/types'
import { mockTeamSummary, mockTeamRanking, mockOpportunities } from '@/mock/manager'

export async function fetchTeamSummary(): Promise<TeamSummary> {
  try {
    const response = await client.get<TeamSummary>('/api/cloud/dashboard/team/summary')
    return response.data
  } catch {
    return mockTeamSummary
  }
}

export async function fetchTeamRanking(): Promise<TeamMember[]> {
  try {
    const response = await client.get<TeamMember[]>('/api/cloud/dashboard/team/ranking')
    return response.data
  } catch {
    return mockTeamRanking
  }
}

export async function fetchOpportunities(): Promise<Opportunity[]> {
  try {
    const response = await client.get<Opportunity[]>('/api/cloud/opportunity/list')
    return response.data
  } catch {
    return mockOpportunities
  }
}
