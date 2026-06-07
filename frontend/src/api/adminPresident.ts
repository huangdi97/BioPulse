import client from './client'
import {
  getMockSummaryCardData,
  getMockSummaryBarData,
  getMockTeamRankings,
  getMockTrendMonthlyData,
  getMockComplianceTrendData,
  getMockComplianceCategoryData,
  type TeamRank,
} from '@/mock/adminPresident'

export type { TeamRank }

export async function fetchPresidentSummary() {
  try {
    const res = await client.get('/api/admin/president/summary')
    return res.data as {
      cardData: ReturnType<typeof getMockSummaryCardData>
      barData: ReturnType<typeof getMockSummaryBarData>
    }
  } catch {
    return {
      cardData: getMockSummaryCardData(),
      barData: getMockSummaryBarData(),
    }
  }
}

export async function fetchPresidentCompliance() {
  try {
    const res = await client.get('/api/admin/president/compliance')
    return res.data as {
      trendData: ReturnType<typeof getMockComplianceTrendData>
      categoryData: ReturnType<typeof getMockComplianceCategoryData>
    }
  } catch {
    return {
      trendData: getMockComplianceTrendData(),
      categoryData: getMockComplianceCategoryData(),
    }
  }
}

export async function fetchPresidentRankings() {
  try {
    const res = await client.get<TeamRank[]>('/api/admin/president/rankings')
    return res.data
  } catch {
    return getMockTeamRankings()
  }
}

export async function fetchPresidentTrend() {
  try {
    const res = await client.get('/api/admin/president/trend')
    return res.data as ReturnType<typeof getMockTrendMonthlyData>
  } catch {
    return getMockTrendMonthlyData()
  }
}
