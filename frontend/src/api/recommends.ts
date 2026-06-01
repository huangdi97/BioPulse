import client from './client'
import type { AiSuggestion } from '@/types'
import { mockRecommends } from '@/mock/recommends'

export async function fetchSuggestions(userId?: number): Promise<AiSuggestion[]> {
  try {
    const response = await client.post<AiSuggestion[]>(
      '/api/cloud/recommend/generate',
      userId ? { user_id: userId } : undefined
    )
    return response.data
  } catch {
    return mockRecommends
  }
}
