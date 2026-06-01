import type { AiSuggestion } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Lightbulb, Target, RefreshCw, Shield } from 'lucide-react'

interface AiSuggestionCardProps {
  suggestions: AiSuggestion[]
  loading?: boolean
  maxItems?: number
  relatedHcpName?: string
}

const typeConfig = {
  visit_priority: {
    icon: Target,
    color: 'text-blue-500',
    bg: 'bg-blue-50',
  },
  follow_up: {
    icon: RefreshCw,
    color: 'text-purple-500',
    bg: 'bg-purple-50',
  },
  insight: {
    icon: Lightbulb,
    color: 'text-yellow-500',
    bg: 'bg-yellow-50',
  },
  compliance_tip: {
    icon: Shield,
    color: 'text-green-500',
    bg: 'bg-green-50',
  },
}

export default function AiSuggestionCard({
  suggestions,
  loading = false,
  maxItems,
  relatedHcpName,
}: AiSuggestionCardProps) {
  const filtered = relatedHcpName
    ? suggestions.filter(
        (s) =>
          !s.relatedHcpName ||
          s.relatedHcpName === relatedHcpName
      )
    : suggestions

  const displayed = maxItems ? filtered.slice(0, maxItems) : filtered

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-yellow-500" />
          AI 建议
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-16 bg-muted rounded-lg" />
            <div className="h-16 bg-muted rounded-lg" />
          </div>
        ) : displayed.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            暂无建议
          </p>
        ) : (
          displayed.map((suggestion) => {
            const config = typeConfig[suggestion.type]
            const Icon = config.icon

            return (
              <div
                key={suggestion.id}
                className="flex gap-3 p-3 rounded-lg border bg-card"
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${config.bg}`}
                >
                  <Icon className={`h-4 w-4 ${config.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">
                      {suggestion.title}
                    </p>
                    {suggestion.relatedHcpName && (
                      <span className="text-xs text-muted-foreground shrink-0">
                        @{suggestion.relatedHcpName}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-1">
                    {suggestion.content}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </CardContent>
    </Card>
  )
}
