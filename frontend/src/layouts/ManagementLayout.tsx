import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  ShieldCheck,
  Trophy,
  TrendingUp,
  BarChart3,
  Users,
  Briefcase,
  ClipboardList,
  UserCircle,
  LogOut,
  Pill,
} from 'lucide-react'

const PRESIDENT_MENU = [
  { to: '/admin/president/summary', label: '概览', icon: LayoutDashboard },
  { to: '/admin/president/compliance', label: '合规', icon: ShieldCheck },
  { to: '/admin/president/rankings', label: '排名', icon: Trophy },
  { to: '/admin/president/trend', label: '趋势', icon: TrendingUp },
  { to: '/admin/president/expense-waste', label: '费用浪费', icon: TrendingUp },
  { to: '/admin/president/visit-fraud', label: '拜访造假', icon: ShieldCheck },
  { to: '/admin/president/management-neglect', label: '管理失职', icon: Briefcase },
  { to: '/admin/president/rectification', label: '整改闭环', icon: ClipboardList },
  { to: '/admin/president/exclusion-gates', label: '排除闸', icon: ShieldCheck },
]

const MANAGER_MENU = [
  { to: '/admin/manager/stats', label: '统计', icon: BarChart3 },
  { to: '/admin/manager/members', label: '成员', icon: Users },
  { to: '/admin/manager/compliance', label: '合规', icon: ShieldCheck },
  { to: '/admin/manager/performance', label: '绩效', icon: Briefcase },
]

const EMPLOYEE_MENU = [
  { to: '/admin/employee/profile', label: '资料', icon: UserCircle },
  { to: '/admin/employee/tasks', label: '任务', icon: ClipboardList },
  { to: '/admin/employee/compliance', label: '合规', icon: ShieldCheck },
  { to: '/admin/employee/performance', label: '绩效', icon: Briefcase },
  { to: '/admin/employee/trend', label: '趋势', icon: TrendingUp },
]

function getMenu(role: string | undefined) {
  switch (role) {
    case 'admin':
      return PRESIDENT_MENU
    case 'manager':
      return MANAGER_MENU
    default:
      return EMPLOYEE_MENU
  }
}

export default function ManagementLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menu = getMenu(user?.role)
  const isActive = (to: string) => location.pathname.startsWith(to)

  return (
    <div className="flex h-screen bg-background">
      <aside className="hidden md:flex flex-col w-56 bg-slate-900 text-slate-100 shrink-0">
        <div className="flex items-center gap-2 px-4 py-4 border-b border-slate-700">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary">
            <Pill className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-sm">管理后台</span>
        </div>
        <nav className="flex-1 py-3 space-y-1 px-2">
          {menu.map((item) => {
            const Icon = item.icon
            const active = isActive(item.to)
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
      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex md:hidden items-center justify-between px-4 py-2 bg-slate-900 text-slate-100 shrink-0">
          <div className="flex items-center gap-2">
            <Pill className="h-5 w-5" />
            <span className="font-semibold text-sm">管理后台</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-300">{user?.username}</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-slate-100 hover:bg-slate-700 h-8 w-8"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </header>
        <nav className="flex md:hidden border-b bg-background dark:bg-gray-900 shrink-0 overflow-x-auto">
          {menu.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive: active }) =>
                  `flex-1 flex flex-col items-center justify-center py-2 min-w-[64px] text-sm transition-colors ${
                    active ? 'text-primary font-medium' : 'text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span className="text-xs mt-0.5 truncate">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
        <header className="hidden md:flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border-b shrink-0">
          {menu.map((item) => {
            if (!isActive(item.to)) return null
            return (
              <div key={item.to} className="flex items-center gap-1 text-sm text-muted-foreground">
                <span>管理后台</span>
                <span className="mx-1">/</span>
                <span className="text-foreground font-medium">{item.label}</span>
              </div>
            )
          })}
        </header>
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
