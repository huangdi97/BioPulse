import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchScenarios, type Scenario } from '@/api/coach'
import { Card, CardContent } from '@/components/ui/card'
import { Play, Clock, BarChart3 } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { FilterDropdown } from '@/components/FilterDropdown'
import { Skeleton } from '@/components/Skeleton'

const DIFFICULTY_MAP: Record<Scenario['difficulty'], { label: string; color: string }> = {
  easy: { label: '简单', color: 'bg-green-50 text-green-700' },
  medium: { label: '中等', color: 'bg-yellow-50 text-yellow-700' },
  hard: { label: '困难', color: 'bg-red-50 text-red-700' },
}

const DIFFICULTY_OPTIONS = ['全部', 'easy', 'medium', 'hard']
const DIFFICULTY_LABELS: Record<string, string> = { '全部': '全部', easy: '简单', medium: '中等', hard: '困难' }

export default function ScenarioList() {
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [difficulty, setDifficulty] = useState('全部')

  useEffect(() => {
    let cancelled = false
    fetchScenarios().then((data) => {
      if (cancelled) return
      setScenarios(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    return scenarios.filter((s) => {
      const matchSearch = !search || s.name.includes(search) || s.description.includes(search) || s.category.includes(search)
      const matchDiff = difficulty === '全部' || s.difficulty === difficulty
      return matchSearch && matchDiff
    })
  }, [scenarios, search, difficulty])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}><CardContent className="p-4"><Skeleton className="h-16 w-full" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">演练场景</h2>
      <SearchBar placeholder="搜索场景名或分类..." value={search} onChange={setSearch} />
      <FilterDropdown
        label="难度"
        value={difficulty}
        options={DIFFICULTY_OPTIONS.map((v) => ({ value: v, label: DIFFICULTY_LABELS[v] }))}
        onChange={setDifficulty}
      />
      <div className="space-y-3">
        {filtered.map((scenario) => {
          const diff = DIFFICULTY_MAP[scenario.difficulty]
          return (
            <Card
              key={scenario.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/coach/sessions`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold">{scenario.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">{scenario.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />{scenario.duration}分钟
                      </span>
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <BarChart3 className="h-3 w-3" />{scenario.category}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${diff.color}`}>
                      {diff.label}
                    </span>
                    <div className="flex items-center justify-center h-10 w-10 rounded-full bg-blue-600 text-white">
                      <Play className="h-4 w-4" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-sm text-muted-foreground">没有找到匹配的场景</div>
      )}
    </div>
  )
}
