import client from './client'
import type { ApprovalRecord } from '@/types'

export async function submitQuotation(data: {
  product: string
  amount: number
  limit_amount?: number
  rep_id?: number
}): Promise<{ quotation_id: string; status: string; message: string }> {
  const res = await client.post('/api/cloud/api/v1/quotation/approve', data)
  return res.data
}

export async function fetchPendingApprovals(): Promise<ApprovalRecord[]> {
  const res = await client.get('/api/cloud/api/v1/quotation/pending')
  return res.data
}

export async function reviewQuotation(
  quotationId: string,
  action: string,
  notes: string = ''
): Promise<{ quotation_id: string; status: string }> {
  const res = await client.post(`/api/cloud/api/v1/quotation/${quotationId}/review`, { action, notes })
  return res.data
}
