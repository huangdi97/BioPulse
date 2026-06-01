import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import {
  Users,
  FileText,
  BookOpen,
  LogOut,
  ClipboardCheck,
  MessageSquare,
} from 'lucide-react'

const sidebarItems = [
  { to: '/assistant/hcps', label: 'HCP列表', icon: Users },
  { to: '/assistant/visits', label: '拜访记录', icon: FileText },
  { to: '/assistant/tasks', label: '任务列表', icon: ClipboardCheck },
  { to: '/assistant/knowledge', label: '知识库', icon: BookOpen },
  { to: '/assistant/qa', label: '问答', icon: MessageSquare },
]

export default function AssistantLayout() {
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
          <div className="flex h-8 w-8 items-center justify-center rounded bg-teal-600">
            <Users className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-sm">拜访助手</span>
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
                    ? 'bg-teal-600 text-white'
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
              {user?.username?.charAt(0) ?? 'A'}
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
            <Users className="h-5 w-5" />
            <span className="font-semibold text-sm">拜访助手</span>
          </div>
          <Button variant="ghost" size="icon" onClick={handleLogout} className="text-slate-100 hover:bg-slate-700">
            <LogOut className="h-4 w-4" />
          </Button>
        </header>

        <nav className="flex md:hidden border-b bg-background shrink-0">
          {sidebarItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  `flex-1 flex flex-col items-center justify-center py-2 text-sm transition-colors ${
                    isActive ? 'text-teal-600 font-medium' : 'text-muted-foreground hover:text-foreground'
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
          <Outlet />
        </main>
      </div>
    </div>
  )
}
