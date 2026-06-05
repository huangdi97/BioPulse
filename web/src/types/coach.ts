export interface Scenario {
  id: number
  name: string
  description: string
  difficulty: "初级" | "中级" | "高级"
  category: "合规" | "拜访" | "异议" | "谈判" | "产品介绍"
  completed: boolean
  score: number
  duration: number
  tags: string[]
}

export interface TrainingRecord {
  id: number
  scenario_name: string
  date: string
  score: number
  duration: number
  weakness: string
  strength: string
}

export interface AbilityDimension {
  name: string
  score: number
  target: number
}

export interface AbilityAssessment {
  dimensions: AbilityDimension[]
  average: number
  suggestions: string[]
}
