import { createContext, useContext, useState, useCallback, type ReactNode } from "react"
import { loginApi, registerApi, setToken } from "../api/client"

interface User {
  id: number
  username: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  error: string | null
  login: (username: string, password: string, scope?: string) => Promise<void>
  register: (username: string, password: string) => Promise<void>
  logout: () => void
  init: () => void
}

const AuthContext = createContext<AuthState | undefined>(undefined)

const STORAGE_KEY = "auth"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const persist = useCallback((t: string, u: User) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: t, user: u }))
    setTokenState(t)
    setToken(t)
    setUser(u)
    setError(null)
  }, [])

  const init = useCallback(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed.token && parsed.user) {
          setTokenState(parsed.token)
          setToken(parsed.token)
          setUser(parsed.user)
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  const login = useCallback(async (username: string, password: string, scope?: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await loginApi(username, password, scope)
      persist(data.token, data.user)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Login failed"
      setError(msg)
      throw e
    } finally {
      setLoading(false)
    }
  }, [persist])

  const register = useCallback(async (username: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await registerApi(username, password)
      persist(data.token, data.user)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Registration failed"
      setError(msg)
      throw e
    } finally {
      setLoading(false)
    }
  }, [persist])

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setTokenState(null)
    setToken(null)
    setUser(null)
    setError(null)
  }, [])

  const value: AuthState = { user, token, loading, error, login, register, logout, init }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
