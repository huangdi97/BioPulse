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

import type { KpiCard, VisitStat, TeamRank, ViolationItem, ResearchKpi, PiSource, ProductMatchStat } from "../types/dashboard"
import type { Paper, PiProfile, Target } from "../types/intel"

export async function getPharmaKpis(): Promise<KpiCard[]> {
  return fetchApi<KpiCard[]>('/dashboard/overview')
}

export async function getVisitTrends(): Promise<VisitStat[]> {
  return fetchApi<VisitStat[]>('/dashboard/visit-trends')
}

export async function getTeamRanks(): Promise<TeamRank[]> {
  return fetchApi<TeamRank[]>('/dashboard/team-ranks')
}

export async function getViolations(): Promise<ViolationItem[]> {
  return fetchApi<ViolationItem[]>('/dashboard/violations')
}

export async function getResearchKpis(): Promise<ResearchKpi[]> {
  return fetchApi<ResearchKpi[]>('/dashboard/research-kpis')
}

export async function getPiSources(): Promise<PiSource[]> {
  return fetchApi<PiSource[]>('/dashboard/pi-sources')
}

export async function getProductMatchStats(): Promise<ProductMatchStat[]> {
  return fetchApi<ProductMatchStat[]>('/dashboard/product-match-stats')
}

export async function getComplianceKpis(): Promise<KpiCard[]> {
  return fetchApi<KpiCard[]>('/dashboard/compliance')
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
