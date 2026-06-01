import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

interface SearchItem {
  label: string
  path: string
  keywords: string[]
}

const SEARCH_ITEMS: SearchItem[] = [
  { label: 'HCP 客户列表', path: '/rep/hcps', keywords: ['hcp', '客户', 'cu'] },
  { label: '任务列表', path: '/rep/tasks', keywords: ['task', '任务', 'rw'] },
  { label: '新建拜访', path: '/rep/visits/new', keywords: ['visit', '拜访', 'bf'] },
  { label: '演练场景', path: '/coach/scenarios', keywords: ['scenario', '场景', 'yl'] },
  { label: '演练记录', path: '/coach/sessions', keywords: ['session', '记录', 'jl'] },
  { label: '评估记录', path: '/coach/assessments', keywords: ['assessment', '评估', 'pg'] },
  { label: '总结反思', path: '/coach/reflections', keywords: ['reflection', '反思', 'fs'] },
  { label: '数据统计', path: '/coach/stats', keywords: ['stats', '统计', 'tj'] },
  { label: '商机列表', path: '/opportunity/opportunities', keywords: ['opportunity', '商机', 'sj'] },
  { label: '投标管理', path: '/opportunity/bidding', keywords: ['bidding', '投标', 'tb'] },
  { label: '联系人', path: '/opportunity/contacts', keywords: ['contact', '联系人', 'lxr'] },
  { label: '趋势分析', path: '/opportunity/trends', keywords: ['trend', '趋势', 'qs'] },
  { label: '商机统计', path: '/opportunity/stats', keywords: ['stats', '统计', 'tj'] },
  { label: 'HCP 助手', path: '/assistant/hcps', keywords: ['hcp', 'assistant', 'zs'] },
  { label: '知识库', path: '/assistant/knowledge', keywords: ['knowledge', '知识库', 'zsk'] },
  { label: '预呼叫', path: '/sales-assistant/precall', keywords: ['precall', '预呼叫', 'yhj'] },
  { label: '内容库', path: '/sales-assistant/content', keywords: ['content', '内容', 'nr'] },
  { label: '策略建议', path: '/sales-assistant/strategy', keywords: ['strategy', '策略', 'cl'] },
  { label: '异议处理', path: '/sales-assistant/objections', keywords: ['objection', '异议', 'yy'] },
  { label: '笔记', path: '/sales-assistant/notes', keywords: ['note', '笔记', 'bj'] },
  { label: '漏斗', path: '/sales-assistant/funnel', keywords: ['funnel', '漏斗', 'ld'] },
  { label: '日程', path: '/sales-assistant/schedule', keywords: ['schedule', '日程', 'rc'] },
  { label: '经理看板', path: '/manager/dashboard', keywords: ['manager', '经理', 'jl'] },
  { label: '合规概览', path: '/manager/compliance', keywords: ['compliance', '合规', 'hg'] },
]

interface GlobalSearchDialogProps {
  open: boolean
  onClose: () => void
}

export function GlobalSearchDialog({ open, onClose }: GlobalSearchDialogProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const results = query.trim()
    ? SEARCH_ITEMS.filter(
        (item) =>
          item.label.toLowerCase().includes(query.toLowerCase()) ||
          item.keywords.some((kw) => kw.toLowerCase().includes(query.toLowerCase()))
      )
    : []

  const handleSelect = useCallback(
    (path: string) => {
      navigate(path)
      onClose()
    },
    [navigate, onClose]
  )

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh]">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-xl border bg-popover shadow-2xl mx-4">
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              autoFocus
              placeholder="搜索页面... (Ctrl+K)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') onClose()
              }}
              className="pl-9 border-0 shadow-none focus-visible:ring-0"
            />
          </div>
        </div>
        {results.length > 0 && (
          <div className="max-h-64 overflow-y-auto p-2">
            {results.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => handleSelect(item.path)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-accent text-left"
              >
                <Search className="h-4 w-4 text-muted-foreground shrink-0" />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        )}
        {query.trim() && results.length === 0 && (
          <div className="p-6 text-center text-sm text-muted-foreground">
            未找到匹配页面
          </div>
        )}
        <div className="px-3 py-2 border-t text-xs text-muted-foreground flex gap-4">
          <span>↑↓ 导航</span>
          <span>Enter 跳转</span>
          <span>Esc 关闭</span>
        </div>
      </div>
    </div>
  )
}
