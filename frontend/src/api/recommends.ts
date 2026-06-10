import client, { withFallback } from './client'
import type { AiSuggestion } from '@/types'
import { mockRecommends } from '@/mock/recommends'

export async function fetchSuggestions(userId?: number): Promise<AiSuggestion[]> {
  return withFallback(
    async () => {
      const response = await client.post<AiSuggestion[]>(
        '/api/cloud/recommend/generate',
        userId ? { user_id: userId } : undefined
      )
      return response.data
    },
    () => mockRecommends
  )
}
