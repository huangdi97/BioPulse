import client, { withFallback } from './client'
import type { TodayRecommendation } from '@/types'

export async function fetchTodayRecommendations(userId?: number): Promise<TodayRecommendation> {
  return withFallback(
    async () => {
      const response = await client.get<TodayRecommendation>('/api/rep/dashboard/today-recommendations', {
        params: userId ? { user_id: userId } : undefined,
      })
      return response.data
    },
    () => ({
      recommendations: [
        { id: 1, title: '跟进A医院王主任', content: '上周拜访后建议跟进产品反馈', type: 'follow_up' },
        { id: 2, title: '竞品动态提醒', content: '竞品X已进入B医院，建议制定应对策略', type: 'competitor_alert' },
      ],
      visit_reasons: [
        { hcp_name: '李医生', reason: '新品上市学术传递', material: '新品手册' },
      ],
      expense_alerts: [
        { expense_id: 101, alert: '昨日交通费超出限额', severity: 'medium' },
      ],
    })
  )
}
