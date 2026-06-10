import client, { withFallback } from './client'
import type { VisitRecord } from '@/types'
import { mockVisits } from '@/mock/visits'

export interface CreateVisitParams {
  hcpId: number
  hcpName: string
  content: string
  visitType: string
}

let mockIdCounter = Math.max(...mockVisits.map((v) => v.id), 0)

export async function createVisit(data: CreateVisitParams): Promise<VisitRecord> {
  return withFallback(
    async () => {
      const response = await client.post<VisitRecord>('/api/assistant/visit', data)
      return response.data
    },
    () => {
      mockIdCounter += 1
      const now = new Date().toISOString().slice(0, 10)
      const record: VisitRecord = {
        id: mockIdCounter,
        hcpId: data.hcpId,
        hcpName: data.hcpName,
        content: data.content,
        visitType: data.visitType,
        createdAt: now,
        complianceStatus: 'passed',
        date: now,
        summary: data.content,
      }
      mockVisits.push(record)
      return record
    }
  )
}

export async function fetchVisitDetail(id: number): Promise<VisitRecord | null> {
  return withFallback(
    async () => {
      const response = await client.get<VisitRecord>(`/api/assistant/visit/${id}`)
      return response.data
    },
    () => mockVisits.find((v) => v.id === id) ?? null
  )
}
