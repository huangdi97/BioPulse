import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  BarChart3,
  Target,
  ShieldCheck,
  LogOut,
  Pill,
  TrendingUp,
  GraduationCap,
  Phone,
  UserPlus,
  ClipboardCheck,
  FileCheck,
  Stethoscope,
  Network,
} from 'lucide-react'

const END_PORTS = [
  { to: '/manager/dashboard', label: '云四端', icon: Pill },
  { to: '/coach', label: '销售教练', icon: GraduationCap },
  { to: '/opportunity', label: '商机', icon: Target },
  { to: '/assistant', label: '拜访助手', icon: UserPlus },
  { to: '/sales-assistant', label: '销售助理', icon: Phone },
]

const sidebarItems = [
  { to: '/manager/dashboard', label: '团队概览', icon: LayoutDashboard },
  { to: '/manager/visits', label: '拜访统计', icon: BarChart3 },
  { to: '/manager/opportunities', label: '商机 Pipeline', icon: Target },
  { to: '/manager/compliance', label: '合规看板', icon: ShieldCheck, disabled: false },
  { to: '/manager/inspection', label: '飞检仪表盘', icon: ClipboardCheck },
  { to: '/manager/inspection/assign', label: '整改分派', icon: ClipboardCheck },
  { to: '/manager/inspection/review', label: '复查确认', icon: ClipboardCheck },
  { to: '/manager/approval', label: '报价审批', icon: FileCheck },
  { to: '/manager/admission', label: '入院Tracker', icon: Stethoscope },
  { to: '/manager/world-model', label: '世界模型', icon: Network },
]

const bottomTabs = [
  { to: '/manager/dashboard', label: '看板', icon: LayoutDashboard },
  { to: '/manager/visits', label: '拜访', icon: BarChart3 },
  { to: '/manager/opportunities', label: '商机', icon: Target },
  { to: '/manager/compliance', label: '合规', icon: ShieldCheck, disabled: false },
  { to: '/manager/inspection', label: '飞检', icon: ClipboardCheck },
  { to: '/manager/approval', label: '审批', icon: FileCheck },
  { to: '/manager/admission', label: '入院', icon: Stethoscope },
]

export default function ManagerLayout() {
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
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-56 bg-slate-900 text-slate-100 shrink-0">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-slate-700">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-sm">管理后台</span>
        </div>

        <nav className="flex-1 py-3 space-y-1 px-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.to)

            if (item.disabled) {
              return (
                <span
                  key={item.to}
                  className="flex items-center gap-3 px-3 py-2 rounded-md text-slate-500 cursor-not-allowed opacity-50"
                >
                  <Icon className="h-4 w-4" />
                  <span className="text-sm">{item.label}</span>
                </span>
              )
            }

            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  active
                    ? 'bg-primary text-primary-foreground'
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
              {user?.username?.charAt(0) ?? '管'}
            </div>
            <span className="text-sm text-slate-300 truncate">{user?.username ?? '管理员'}</span>
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

      {/* Mobile: top header + bottom tabs */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Mobile Top Bar */}
        <header className="flex md:hidden flex-col bg-slate-900 text-slate-100 shrink-0">
          <div className="flex items-center justify-between px-4 py-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              <span className="font-semibold text-sm">管理后台</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm">{user?.username}</span>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                className="text-slate-100 hover:bg-slate-700"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <nav className="flex items-center gap-0.5 px-2 pb-1.5 overflow-x-auto">
            {END_PORTS.map((end) => {
              const Icon = end.icon
              return (
                <NavLink
                  key={end.to}
                  to={end.to}
                  className={({ isActive }) =>
                    `flex items-center gap-1 px-2 py-1 rounded text-xs whitespace-nowrap transition-colors ${
                      isActive
                        ? 'bg-white/20 font-medium'
                        : 'hover:bg-white/10'
                    }`
                  }
                >
                  <Icon className="h-3 w-3" />
                  <span>{end.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </header>

        {/* Desktop top bar (minimal) */}
        <header className="hidden md:flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b shrink-0">
          <nav className="flex items-center gap-1">
            {END_PORTS.map((end) => {
              const Icon = end.icon
              return (
                <NavLink
                  key={end.to}
                  to={end.to}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs whitespace-nowrap transition-colors ${
                      isActive
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                    }`
                  }
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{end.label}</span>
                </NavLink>
              )
            })}
          </nav>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.username ?? '管理员'}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-1" />
              退出
            </Button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>

        {/* Mobile Bottom Tabs */}
        <nav className="flex md:hidden border-t bg-background dark:bg-gray-900 shrink-0">
          {bottomTabs.map((tab) => {
            const Icon = tab.icon
            if (tab.disabled) {
              return (
                <span
                  key={tab.to}
                  className="flex-1 flex flex-col items-center justify-center py-2 opacity-40"
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs text-muted-foreground mt-1">{tab.label}</span>
                </span>
              )
            }
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.to === '/manager/dashboard'}
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
