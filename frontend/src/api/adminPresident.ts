import client, { withFallback } from './client'
import {
  getMockSummaryCardData,
  getMockSummaryBarData,
  getMockTeamRankings,
  getMockTrendMonthlyData,
  getMockComplianceTrendData,
  getMockComplianceCategoryData,
  getMockExpenseWasteData,
  getMockVisitFraudData,
  getMockManagementNeglectData,
  getMockRectificationData,
  getMockExclusionGates,
  type TeamRank,
} from '@/mock/adminPresident'

export type { TeamRank }

export async function fetchPresidentSummary() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/summary')
      return res.data as {
        cardData: ReturnType<typeof getMockSummaryCardData>
        barData: ReturnType<typeof getMockSummaryBarData>
      }
    },
    () => ({
      cardData: getMockSummaryCardData(),
      barData: getMockSummaryBarData(),
    })
  )
}

export async function fetchPresidentCompliance() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/compliance')
      return res.data as {
        trendData: ReturnType<typeof getMockComplianceTrendData>
        categoryData: ReturnType<typeof getMockComplianceCategoryData>
      }
    },
    () => ({
      trendData: getMockComplianceTrendData(),
      categoryData: getMockComplianceCategoryData(),
    })
  )
}

export async function fetchPresidentRankings() {
  return withFallback(
    async () => {
      const res = await client.get<TeamRank[]>('/api/admin/president/rankings')
      return res.data
    },
    () => getMockTeamRankings()
  )
}

export async function fetchPresidentTrend() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/trend')
      return res.data as ReturnType<typeof getMockTrendMonthlyData>
    },
    () => getMockTrendMonthlyData()
  )
}

export async function fetchExpenseWaste() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/expense-waste')
      return res.data as ReturnType<typeof getMockExpenseWasteData>
    },
    () => getMockExpenseWasteData()
  )
}

export async function fetchVisitFraud() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/visit-fraud')
      return res.data as ReturnType<typeof getMockVisitFraudData>
    },
    () => getMockVisitFraudData()
  )
}

export async function fetchManagementNeglect() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/management-neglect')
      return res.data as ReturnType<typeof getMockManagementNeglectData>
    },
    () => getMockManagementNeglectData()
  )
}

export async function fetchRectification() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/rectification')
      return res.data as ReturnType<typeof getMockRectificationData>
    },
    () => getMockRectificationData()
  )
}

export async function fetchExclusionGates() {
  return withFallback(
    async () => {
      const res = await client.get('/api/admin/president/exclusion-gates')
      return res.data as ReturnType<typeof getMockExclusionGates>
    },
    () => getMockExclusionGates()
  )
}
