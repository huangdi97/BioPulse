import client, { withFallback } from './client'
import type { HCP, VisitRecord } from '@/types'
import { mockHcps } from '@/mock/hcps'

export interface HcpQueryParams {
  search?: string
  dept?: string
  region?: string
  priority?: string
}

export async function fetchHcps(params?: HcpQueryParams): Promise<HCP[]> {
  return withFallback(
    async () => {
      const response = await client.get<HCP[]>('/api/assistant/hcp/list', { params })
      return response.data
    },
    () => {
      let result = [...mockHcps]
      if (params) {
        const { search, dept, region, priority } = params
        if (search) {
          const kw = search.toLowerCase()
          result = result.filter(
            (h) => h.name.includes(kw) || h.hospital.toLowerCase().includes(kw)
          )
        }
        if (dept && dept !== '全部') {
          result = result.filter((h) => h.dept === dept)
        }
        if (region && region !== '全部') {
          result = result.filter((h) => h.region === region)
        }
        if (priority && priority !== '全部') {
          result = result.filter((h) => h.priority === priority)
        }
      }
      return result
    }
  )
}

export async function fetchHcpDetail(id: number): Promise<HCP | null> {
  return withFallback(
    async () => {
      const response = await client.get<HCP>(`/api/assistant/hcp/${id}`)
      return response.data
    },
    () => mockHcps.find((h) => h.id === id) ?? null
  )
}

export async function fetchVisitHistory(hcpId: number): Promise<VisitRecord[]> {
  return withFallback(
    async () => {
      const response = await client.get<VisitRecord[]>('/api/assistant/visit', {
        params: { hcp_id: hcpId },
      })
      return response.data
    },
    () => []
  )
}
