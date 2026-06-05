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

export async function getPharmaKpis(): Promise<KpiCard[]> {
  return pharmaKpis
}

export async function getVisitTrends(): Promise<VisitStat[]> {
  return visitTrends
}

export async function getTeamRanks(): Promise<TeamRank[]> {
  return teamRanks
}

export async function getViolations(): Promise<ViolationItem[]> {
  return violations
}

export async function getResearchKpis(): Promise<ResearchKpi[]> {
  return researchKpis
}

export async function getPiSources(): Promise<PiSource[]> {
  return piSources
}

export async function getProductMatchStats(): Promise<ProductMatchStat[]> {
  return productMatchStats
}

export async function getComplianceKpis(): Promise<KpiCard[]> {
  return complianceKpis
}
