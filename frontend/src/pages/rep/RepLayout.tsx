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
} from 'lucide-react'

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
    <div className="flex flex-col h-screen bg-background">
      <header className="flex items-center justify-between px-4 py-2 bg-primary text-primary-foreground shrink-0">
        <div className="flex items-center gap-2">
          <Pill className="h-5 w-5" />
          <span className="font-semibold text-sm">云四端</span>
        </div>
        <div className="flex items-center gap-3">
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

      <main className="flex-1 overflow-y-auto p-4">
        <Outlet />
      </main>

      <nav className="flex border-t bg-background shrink-0">
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
  )
}
