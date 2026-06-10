import client, { withFallback } from './client'
import type { ScanResult, Violation, ComplianceDashboard, ComplianceRecord, AuditEntry } from '@/types'
import {
  mockComplianceDashboard,
  mockComplianceRecords,
  mockAuditChain,
} from '@/mock/compliance'

const keywordRules: Record<string, Omit<Violation, 'keyword'>> = {
  '治愈': { category: '虚假宣传', riskLevel: 'critical', suggestion: '建议使用"有效改善"或"辅助治疗"替代' },
  '根治': { category: '虚假宣传', riskLevel: 'critical', suggestion: '建议使用"有效控制"或"显著改善"替代' },
  '最安全': { category: '违规宣称', riskLevel: 'high', suggestion: '建议使用"安全性良好"替代' },
  '无副作用': { category: '违规宣称', riskLevel: 'high', suggestion: '建议使用"安全性良好"或"不良反应发生率低"替代' },
  '优于竞品': { category: '不正当竞争', riskLevel: 'medium', suggestion: '建议使用"具有临床优势"或"提供差异化价值"替代' },
  '特效': { category: '夸大宣传', riskLevel: 'high', suggestion: '建议使用"疗效确切"或"临床验证有效"替代' },
}

function fallbackScan(content: string): ScanResult {
  const violations: Violation[] = []

  for (const [keyword, rule] of Object.entries(keywordRules)) {
    if (content.includes(keyword)) {
      violations.push({
        keyword,
        ...rule,
      })
    }
  }

  if (violations.length === 0) {
    return { passed: true, riskLevel: 'low', violations: [], score: 100 }
  }

  const riskLevels = violations.map((v) => {
    switch (v.riskLevel) {
      case 'critical': return 4
      case 'high': return 3
      case 'medium': return 2
      default: return 1
    }
  })

  const maxRisk = Math.max(...riskLevels)
  let riskLevel: ScanResult['riskLevel'] = 'low'
  if (maxRisk >= 4) riskLevel = 'critical'
  else if (maxRisk >= 3) riskLevel = 'high'
  else if (maxRisk >= 2) riskLevel = 'medium'

  const score = Math.max(0, 100 - violations.length * 25)

  return { passed: false, riskLevel, violations, score }
}

export async function scanContent(content: string): Promise<ScanResult> {
  return withFallback(
    async () => {
      const response = await client.post<ScanResult>('/api/cloud/compliance-v2/scan', { content })
      return response.data
    },
    () => fallbackScan(content)
  )
}

export async function fetchComplianceDashboard(): Promise<ComplianceDashboard> {
  return withFallback(
    async () => {
      const response = await client.get<ComplianceDashboard>('/api/cloud/compliance-v2/dashboard')
      return response.data
    },
    () => mockComplianceDashboard
  )
}

export async function fetchComplianceRecords(
  params?: { status?: string; riskLevel?: string; repName?: string }
): Promise<ComplianceRecord[]> {
  return withFallback(
    async () => {
      const response = await client.get<ComplianceRecord[]>('/api/cloud/compliance-v2/records', { params })
      return response.data
    },
    () => {
      let records = [...mockComplianceRecords]
      if (params?.status && params.status !== 'all') {
        records = records.filter((r) => r.status === params.status)
      }
      if (params?.riskLevel && params.riskLevel !== 'all') {
        records = records.filter((r) => r.riskLevel === params.riskLevel)
      }
      if (params?.repName) {
        records = records.filter((r) => r.repName.includes(params.repName!))
      }
      return records
    }
  )
}

export async function fetchComplianceRecordDetail(id: number): Promise<ComplianceRecord | null> {
  return withFallback(
    async () => {
      const response = await client.get<ComplianceRecord>(`/api/cloud/compliance-v2/records/${id}`)
      return response.data
    },
    () => mockComplianceRecords.find((r) => r.id === id) ?? null
  )
}

export async function fetchAuditChain(entityType: string, entityId: number): Promise<AuditEntry[]> {
  return withFallback(
    async () => {
      const response = await client.get<AuditEntry[]>(
        `/api/cloud/compliance-v2/audit-chain/${entityType}/${entityId}`
      )
      return response.data
    },
    () => mockAuditChain
  )
}
