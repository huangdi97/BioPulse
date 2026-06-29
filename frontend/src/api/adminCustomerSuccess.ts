import client, { withFallback } from './client'

export interface AtRiskRep {
  name: string
  lastLogin: string
  days: number
}

export async function fetchHealthScore(): Promise<number> {
  return withFallback(
    async () => {
      const res = await client.get('/api/v1/customer-success/health-score')
      return res.data as number
    },
    () => 87
  )
}

export async function fetchUsageTrend(): Promise<string> {
  return withFallback(
    async () => {
      const res = await client.get('/api/v1/customer-success/usage-trend')
      return res.data as string
    },
    () => 'Monthly active users increased by 12% compared to last quarter.'
  )
}

export async function fetchAtRiskReps(): Promise<AtRiskRep[]> {
  return withFallback(
    async () => {
      const res = await client.get('/api/v1/customer-success/at-risk-reps')
      return res.data as AtRiskRep[]
    },
    () => [
      { name: 'Zhang Wei', lastLogin: '2026-06-20', days: 9 },
      { name: 'Li Ming', lastLogin: '2026-06-18', days: 11 },
      { name: 'Wang Fang', lastLogin: '2026-06-15', days: 14 },
      { name: 'Chen Jie', lastLogin: '2026-06-10', days: 19 },
      { name: 'Liu Yang', lastLogin: '2026-06-05', days: 24 },
    ]
  )
}

export async function fetchNPS(): Promise<number> {
  return withFallback(
    async () => {
      const res = await client.get('/api/v1/customer-success/nps')
      return res.data as number
    },
    () => 72
  )
}