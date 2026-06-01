import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-bold">欢迎！{user?.username}</h1>
        <Button onClick={logout}>退出登录</Button>
      </div>
    </div>
  )
}
