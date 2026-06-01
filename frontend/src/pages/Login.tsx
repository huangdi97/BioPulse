import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    const errors: { username?: string; password?: string } = {}
    if (!username.trim()) errors.username = '请输入用户名'
    if (!password) errors.password = '请输入密码'
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }
    setFieldErrors({})
    setLoading(true)
    try {
      const user = await login(username, password)
      if (user.role === 'manager' || user.role === 'admin') {
        navigate('/manager/dashboard')
      } else {
        navigate('/rep/dashboard')
      }
    } catch {
      setError('登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-muted/30">
      <Card className="w-full max-w-sm shadow-lg">
        <CardHeader>
          <CardTitle>登录</CardTitle>
          <CardDescription>请输入您的用户名和密码</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                <span className="text-red-500 mr-1">*</span>用户名
              </label>
              <Input
                type="text"
                placeholder="请输入用户名"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value)
                  if (fieldErrors.username) setFieldErrors((p) => ({ ...p, username: undefined }))
                }}
                className={fieldErrors.username ? 'border-red-500' : ''}
              />
              {fieldErrors.username && (
                <p className="flex items-center gap-1 text-xs text-red-500">
                  <AlertCircle className="h-3 w-3" />
                  {fieldErrors.username}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                <span className="text-red-500 mr-1">*</span>密码
              </label>
              <Input
                type="password"
                placeholder="请输入密码"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }))
                }}
                className={fieldErrors.password ? 'border-red-500' : ''}
              />
              {fieldErrors.password && (
                <p className="flex items-center gap-1 text-xs text-red-500">
                  <AlertCircle className="h-3 w-3" />
                  {fieldErrors.password}
                </p>
              )}
            </div>
            {error && <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>}
            <Button type="submit" className="w-full" loading={loading}>
              {loading ? '登录中...' : '登录'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
