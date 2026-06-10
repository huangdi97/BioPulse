import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  Users,
  ClipboardList,
  ClipboardCheck,
  LogOut,
  Pill,
  GraduationCap,
  Target,
  Phone,
  UserPlus,
} from 'lucide-react'

const END_PORTS = [
  { to: '/rep/dashboard', label: '云四端', icon: Pill },
  { to: '/coach', label: '销售教练', icon: GraduationCap },
  { to: '/opportunity', label: '商机', icon: Target },
  { to: '/assistant', label: '拜访助手', icon: UserPlus },
  { to: '/sales-assistant', label: '销售助理', icon: Phone },
]

export default function RepLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const tabs = [
    {
      to: '/rep/dashboard',
      label: '看板',
      icon: LayoutDashboard,
      disabled: false,
    },
    {
      to: '/rep/tasks',
      label: '任务',
      icon: ClipboardCheck,
      disabled: false,
    },
    {
      to: '/rep/hcps',
      label: '客户',
      icon: Users,
      disabled: false,
    },
    {
      to: '/rep/visits',
      label: '拜访记录',
      icon: ClipboardList,
      disabled: false,
    },
  ]

  return (
    <div className="flex h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-56 bg-slate-900 text-slate-100 shrink-0">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-slate-700">
          <Pill className="h-5 w-5 text-primary-foreground" />
          <span className="font-semibold text-sm">云四端</span>
        </div>
        <nav className="flex-1 py-3 space-y-1 px-2">
          {END_PORTS.map((end) => {
            const Icon = end.icon
            return (
              <NavLink
                key={end.to}
                to={end.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{end.label}</span>
              </NavLink>
            )
          })}
        </nav>
        <div className="px-3 py-3 border-t border-slate-700">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-600 text-xs text-white">
              {user?.username?.charAt(0) ?? 'R'}
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

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Mobile header */}
        <header className="flex md:hidden items-center justify-between px-4 py-2 bg-primary text-primary-foreground shrink-0">
          <div className="flex items-center gap-2">
            <Pill className="h-5 w-5" />
              <span className="font-semibold text-sm">云四端</span>
          </div>
          <div className="flex items-center gap-3 dark:text-slate-100">
            <span className="text-sm">{user?.username}</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-primary-foreground hover:bg-primary-foreground/10"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Mobile port nav */}
        <nav className="flex md:hidden items-center gap-0.5 px-2 py-1.5 bg-primary/90 text-primary-foreground shrink-0 overflow-x-auto">
          {END_PORTS.map((end) => {
            const Icon = end.icon
            return (
              <NavLink
                key={end.to}
                to={end.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs whitespace-nowrap transition-colors ${
                    isActive
                      ? 'bg-white/20 font-medium'
                      : 'hover:bg-white/10'
                  }`
                }
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{end.label}</span>
              </NavLink>
            )
          })}
        </nav>

        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>

        {/* Mobile bottom tabs */}
        <nav className="flex md:hidden border-t bg-background dark:bg-gray-900 shrink-0">
          {tabs.map((tab) => {
            const Icon = tab.icon
            if (tab.disabled) {
              return (
                <span
                  key={tab.to}
                  className="flex-1 flex flex-col items-center justify-center py-2 text-muted-foreground cursor-not-allowed opacity-40"
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs mt-1">{tab.label}</span>
                </span>
              )
            }
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.to === '/rep/dashboard'}
                className={({ isActive }) =>
                  `flex-1 flex flex-col items-center justify-center py-2 text-sm transition-colors ${
                    isActive
                      ? 'text-primary font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs mt-1">{tab.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
