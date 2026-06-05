let baseURL = "http://localhost:8000"
let token: string | null = null

export function setBaseURL(url: string) {
  baseURL = url
}

export function setToken(t: string | null) {
  token = t
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  const res = await fetch(`${baseURL}${path}`, { ...options, headers })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

import {
  pharmaKpis,
  visitTrends,
  teamRanks,
  violations,
  researchKpis,
  piSources,
  productMatchStats,
  complianceKpis,
} from "./mockData"
import type { KpiCard, VisitStat, TeamRank, ViolationItem, ResearchKpi, PiSource, ProductMatchStat } from "../types/dashboard"
import type { Paper, PiProfile, Target } from "./mockIntel"

export async function getPharmaKpis(): Promise<KpiCard[]> {
  try {
    const data = await fetchApi<Record<string, unknown>>('/api/demo/dashboard')
    return pharmaKpis.map((kpi, i) => {
      if (i === 1 && data.compliance_rate !== undefined) {
        return { ...kpi, value: data.compliance_rate as string | number }
      }
      if (i === 2 && data.user_count !== undefined) {
        return { ...kpi, value: data.user_count as string | number }
      }
      return kpi
    })
  } catch {
    return pharmaKpis
  }
}

export async function getVisitTrends(): Promise<VisitStat[]> {
  try {
    const data = await fetchApi<{ dates: string[]; counts: number[]; pass_rates: number[] }>('/api/demo/visit-trends')
    return data.dates.map((date, i) => ({
      date,
      count: data.counts[i],
      passRate: data.pass_rates[i],
    }))
  } catch {
    return visitTrends
  }
}

export async function getTeamRanks(): Promise<TeamRank[]> {
  try {
    const data = await fetchApi<{ ranks: { name: string; visits: number; compliance_rate: number; deals: number }[] }>('/api/demo/team-ranks')
    return data.ranks.map(r => ({
      name: r.name,
      visits: r.visits,
      complianceRate: r.compliance_rate,
      deals: r.deals,
    }))
  } catch {
    return teamRanks
  }
}

export async function getViolations(): Promise<ViolationItem[]> {
  try {
    const data = await fetchApi<{ violations: { id: number; rep_name: string; type: string; detail: string; severity: string; date: string; status: string }[] }>('/api/demo/violations')
    return data.violations.map(v => ({
      id: v.id,
      repName: v.rep_name,
      type: v.type,
      detail: v.detail,
      severity: v.severity as "high" | "medium" | "low",
      date: v.date,
      status: v.status as "pending" | "resolved",
    }))
  } catch {
    return violations
  }
}

export async function getResearchKpis(): Promise<ResearchKpi[]> {
  try {
    const data = await fetchApi<{ kpis: ResearchKpi[] }>('/api/demo/research-kpis')
    return data.kpis
  } catch {
    return researchKpis
  }
}

export async function getPiSources(): Promise<PiSource[]> {
  try {
    const data = await fetchApi<{ pi_sources: { name: string; institution: string; matches: number; last_activity: string }[] }>('/api/demo/pi-sources')
    return data.pi_sources.map(s => ({
      name: s.name,
      institution: s.institution,
      matches: s.matches,
      lastActivity: s.last_activity,
    }))
  } catch {
    return piSources
  }
}

export async function getProductMatchStats(): Promise<ProductMatchStat[]> {
  try {
    const data = await fetchApi<{ categories: ProductMatchStat[] }>('/api/demo/product-match-stats')
    return data.categories
  } catch {
    return productMatchStats
  }
}

export async function getComplianceKpis(): Promise<KpiCard[]> {
  try {
    const data = await fetchApi<Record<string, unknown>>('/api/demo/dashboard/compliance')
    return complianceKpis.map((kpi, i) => {
      if (i === 0 && data.total !== undefined) {
        return { ...kpi, value: data.total as string | number }
      }
      if (i === 1 && data.pass_rate !== undefined) {
        return { ...kpi, value: data.pass_rate as string | number }
      }
      if (i === 2 && data.failed !== undefined) {
        return { ...kpi, value: data.failed as string | number, trend: 'down' as const }
      }
      return kpi
    })
  } catch {
    return complianceKpis
  }
}

let intelBaseURL = "http://localhost:8006"

export function setIntelBaseURL(url: string) {
  intelBaseURL = url
}

async function fetchIntelApi<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options?.headers as Record<string, string>),
    }
    const res = await fetch(`${intelBaseURL}${path}`, { ...options, headers })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getIntelPapers(q = '', page = 1, pageSize = 5) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  const json = await fetchIntelApi<{ code: number; data: { items: Paper[]; total: number } }>(`/api/intel/papers?${params}`)
  if (json?.code === 0 && json.data) return json.data
  return { items: [], total: 0, page: 1 }
}

export async function getIntelPiProfiles(q = '', page = 1, pageSize = 10) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  const json = await fetchIntelApi<{ code: number; data: { items: PiProfile[]; total: number } }>(`/api/intel/pi?${params}`)
  if (json?.code === 0 && json.data) return json.data
  return { items: [], total: 0, page: 1 }
}

export async function getIntelTargets(category = '', sortBy = 'paper_count', sortDir = 'desc') {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  params.set('sort_by', sortBy)
  params.set('sort_dir', sortDir)
  const json = await fetchIntelApi<{ code: number; data: Target[] }>(`/api/intel/targets?${params}`)
  if (json?.code === 0 && json.data) return json.data
  return []
}

export async function getIntelTargetCategories() {
  const json = await fetchIntelApi<{ code: number; data: string[] }>('/api/intel/targets/categories')
  if (json?.code === 0 && json.data) return ['全部', ...json.data]
  return ['全部']
}

interface AuthResponse {
  token: string
  user: { id: number; username: string }
}

export async function loginApi(username: string, password: string, scope?: string): Promise<AuthResponse> {
  const body: Record<string, string> = { username, password }
  if (scope) body.scope = scope
  const res = await fetch(`${baseURL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `Login failed (${res.status})`)
  }
  return res.json()
}

export async function changePasswordApi(username: string, old_password: string, new_password: string): Promise<void> {
  const body = { username, old_password, new_password }
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  const res = await fetch(`${baseURL}/auth/change-password`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `Change password failed (${res.status})`)
  }
}

export async function registerApi(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${baseURL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `Register failed (${res.status})`)
  }
  return res.json()
}

// ── Training Coach API (Cloud API, /training-coach/*) ──

interface CoachApiEnvelope<T> {
  code: number
  message: string
  data: T
}

async function fetchCoachApi<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const json = await fetchApi<CoachApiEnvelope<T>>(`/training-coach${path}`, options)
    if (json && json.code === 0 && json.data !== undefined) {
      return json.data
    }
    return null
  } catch {
    return null
  }
}

export async function getCoachModules(): Promise<any[]> {
  const data = await fetchCoachApi<any[]>('/modules')
  return data || []
}

export async function getCoachSessions(userId?: number, page = 1, pageSize = 50): Promise<{ items: any[]; total: number }> {
  const params = new URLSearchParams()
  if (userId) params.set('user_id', String(userId))
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  const data = await fetchCoachApi<any>(`/sessions?${params}`)
  if (data && data.items) return { items: data.items, total: data.total }
  return { items: [], total: 0 }
}

export async function getCoachDashboard(): Promise<Record<string, unknown> | null> {
  return fetchCoachApi<Record<string, unknown>>('/dashboard')
}
