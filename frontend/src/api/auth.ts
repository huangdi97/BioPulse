import client from './client'
import type { LoginResponse } from '@/types'

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await client.post<LoginResponse>('/auth/login', { username, password })

  return response.data
}
