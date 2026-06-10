import type { ApprovalRecord } from '@/types'

export const mockApprovals: ApprovalRecord[] = [
  {
    id: 1,
    quotation_id: 'q-a1b2c3d4',
    rep_name: '赵建国',
    product: '瑞达新药注射液',
    amount: 580000,
    limit_amount: 500000,
    status: 'pending_approval',
    created_at: '2026-06-10 09:30',
  },
  {
    id: 2,
    quotation_id: 'q-e5f6g7h8',
    rep_name: '钱晓峰',
    product: '注射用瑞舒康',
    amount: 1200000,
    limit_amount: 800000,
    status: 'pending_approval',
    created_at: '2026-06-09 14:20',
  },
]
