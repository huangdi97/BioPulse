import { Outlet } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import type { ReactNode } from 'react'

interface RoleRouteProps {
  allowedRoles: string[]
  children?: ReactNode
}

export default function RoleRoute({ allowedRoles, children }: RoleRouteProps) {
  const { user } = useAuth()
  const role = user?.role

  if (!role) return null

  if (allowedRoles.includes(role) || role === 'admin') {
    return children ? <>{children}</> : <Outlet />
  }

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <div className="text-6xl font-bold text-muted-foreground">403</div>
        <h1 className="text-2xl font-semibold text-foreground">禁止访问</h1>
        <p className="text-muted-foreground">
          您没有权限访问此页面
        </p>
      </div>
    </div>
  )
}
