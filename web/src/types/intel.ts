export interface TargetTrend {
  month: string
  count: number
}

export interface Target {
  id: number
  name: string
  category: string
  paper_count: number
  trial_count: number
  growth: number
  trend_data: TargetTrend[]
}

export interface Paper {
  id: number
  title: string
  authors: string[]
  journal: string
  year: number
  citations: number
  abstract?: string
  keywords?: string[]
  doi?: string
  pmid?: string
  relevance?: number
}

export interface PiProfile {
  id: number
  name: string
  institution: string
  department?: string
  title?: string
  h_index?: number
  papers?: number
  paper_count?: number
  grants?: string[]
  research_areas?: string[]
  activity_score?: number
  avatar?: string
}
