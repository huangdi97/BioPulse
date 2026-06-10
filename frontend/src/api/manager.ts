import client, { withFallback } from './client'
import type { TeamSummary, TeamMember, Opportunity } from '@/types'
import { mockTeamSummary, mockTeamRanking, mockOpportunities } from '@/mock/manager'

export async function fetchTeamSummary(): Promise<TeamSummary> {
  return withFallback(
    async () => {
      const response = await client.get<TeamSummary>('/api/cloud/dashboard/team/summary')
      return response.data
    },
    () => mockTeamSummary
  )
}

export async function fetchTeamRanking(): Promise<TeamMember[]> {
  return withFallback(
    async () => {
      const response = await client.get<TeamMember[]>('/api/cloud/dashboard/team/ranking')
      return response.data
    },
    () => mockTeamRanking
  )
}

export async function fetchOpportunities(): Promise<Opportunity[]> {
  return withFallback(
    async () => {
      const response = await client.get<Opportunity[]>('/api/cloud/opportunity/list')
      return response.data
    },
    () => mockOpportunities
  )
}
