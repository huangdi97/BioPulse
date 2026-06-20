import type { User } from '@/types'

export interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<Partial<User>>
  logout: () => void
  isAuthenticated: boolean
}