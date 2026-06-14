import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import {
  Phone,
  FolderOpen,
  Lightbulb,
  FileText,
  Filter,
  LogOut,
  BarChart3,
  Calendar,
} from 'lucide-react'
import AgentSummaryCard from '../../components/AgentSummaryCard'
import AgentInsightBar from '../../components/AgentInsightBar'

const sidebarItems = [
  { to: '/sales-assistant/precall', label: '预呼叫', icon: Phone },
  { to: '/sales-assistant/content', label: '内容库', icon: FolderOpen },
  { to: '/sales-assistant/strategy', label: '策略建议', icon: Lightbulb },
  { to: '/sales-assistant/objections', label: '异议处理', icon: FileText },
  { to: '/sales-assistant/notes', label: '笔记', icon: Filter },
  { to: '/sales-assistant/funnel', label: '销售漏斗', icon: BarChart3 },
  { to: '/sales-assistant/schedule', label: '日程', icon: Calendar },
]

export default function SalesAssistantLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (to: string) => location.pathname.startsWith(to)

  return (
    <div className="flex h-screen bg-background">
      <aside className="hidden md:flex flex-col w-56 bg-slate-900 text-slate-100 shrink-0">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-slate-700">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-amber-600">
            <Phone className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-sm">销售助理</span>
        </div>

        <nav className="flex-1 py-3 space-y-1 px-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.to)
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  active
                    ? 'bg-amber-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        <div className="px-3 py-3 border-t border-slate-700">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-600 text-xs text-white">
              {user?.username?.charAt(0) ?? 'S'}
            </div>
            <span className="text-sm text-slate-300 truncate">{user?.username}</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="ml-auto text-slate-400 hover:text-white hover:bg-slate-800 h-7 w-7"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex md:hidden items-center justify-between px-4 py-2 bg-slate-900 text-slate-100 shrink-0">
          <div className="flex items-center gap-2">
            <Phone className="h-5 w-5" />
            <span className="font-semibold text-sm">销售助理</span>
          </div>
          <Button variant="ghost" size="icon" onClick={handleLogout} className="text-slate-100 hover:bg-slate-700">
            <LogOut className="h-4 w-4" />
          </Button>
        </header>

        <nav className="flex md:hidden border-b bg-background shrink-0">
          {sidebarItems.slice(0, 5).map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  `flex-1 flex flex-col items-center justify-center py-2 text-sm transition-colors ${
                    isActive ? 'text-amber-600 font-medium' : 'text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span className="text-xs mt-0.5">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        <main className="flex-1 overflow-y-auto p-4">
          <AgentSummaryCard title='销售洞察' agentKey='sales_suggestion' pageId='sales_assistant' variant='suggestion' />
          <AgentInsightBar pageId="sales_assistant" />
          <Outlet />
        </main>
      </div>
    </div>
  )
}
