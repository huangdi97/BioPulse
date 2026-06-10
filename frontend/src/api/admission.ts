import client from './client'
import type { AdmissionRecord } from '@/types'

export async function createAdmission(data: {
  hospital_name: string
  department: string
  product: string
  meeting_date?: string
  notes?: string
}): Promise<AdmissionRecord> {
  const res = await client.post('/api/cloud/api/v1/admission', data)
  return res.data
}

export async function fetchAdmissions(params?: {
  status?: string
  rep_id?: number
}): Promise<AdmissionRecord[]> {
  const res = await client.get('/api/cloud/api/v1/admission', { params })
  return res.data
}

export async function fetchAdmissionDetail(id: number): Promise<AdmissionRecord> {
  const res = await client.get(`/api/cloud/api/v1/admission/${id}`)
  return res.data
}

export async function updateAdmissionStatus(id: number, status: string): Promise<AdmissionRecord> {
  const res = await client.put(`/api/cloud/api/v1/admission/${id}/status`, { status })
  return res.data
}
