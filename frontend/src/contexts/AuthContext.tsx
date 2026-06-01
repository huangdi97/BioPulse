import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { login as loginApi } from '@/api/auth'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<Partial<User>>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

function parseToken(token: string): User | null {
  const parts = token.split('.')
  if (parts.length !== 3) {
    return null
  }
  try {
    const payload = JSON.parse(atob(parts[1]))
    if (payload.sub) {
      return { username: payload.sub, role: payload.role }
    }
    return null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    if (token) {
      setUser(parseToken(token))
    } else {
      setUser(null)
    }
  }, [token])

  const login = useCallback(async (username: string, password: string) => {
    const data = await loginApi(username, password)
    localStorage.setItem('token', data.access_token)
    const parsedUser = parseToken(data.access_token)
    setToken(data.access_token)
    setUser(parsedUser)
    return parsedUser ?? undefined
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }, [])

  const isAuthenticated = !!token

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
