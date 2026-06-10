import type { AdmissionRecord } from '@/types'

export const mockAdmissions: AdmissionRecord[] = [
  {
    id: 1,
    hospital_name: '北京协和医院',
    department: '内分泌科',
    product: '瑞达新药注射液',
    status: '药事会排期',
    meeting_date: '2026-07-15',
    notes: '张主任已同意安排药事会讨论',
    rep_name: '赵建国',
    created_at: '2026-06-01',
  },
  {
    id: 2,
    hospital_name: '复旦大学附属中山医院',
    department: '心内科',
    product: '注射用瑞舒康',
    status: '待提交',
    meeting_date: null,
    notes: '需准备临床资料',
    rep_name: '钱晓峰',
    created_at: '2026-06-05',
  },
  {
    id: 3,
    hospital_name: '上海瑞金医院',
    department: '消化内科',
    product: '消化产品线准入',
    status: '已通过',
    meeting_date: '2026-05-20',
    notes: '药事会已通过，待签订合同',
    rep_name: '赵建国',
    created_at: '2026-05-01',
  },
]
