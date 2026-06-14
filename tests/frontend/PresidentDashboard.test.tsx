import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import PresidentDashboard from '@/pages/admin/president/PresidentDashboard'

const mockSummary = { summary: '本月整体合规率提升5.2%，异常事件环比下降30%。华东大区表现优异，西北区域需重点关注。' }
const mockKpi = { complianceRate: 94.2, visitCount: 1256, anomalyCount: 18 }
const mockTrend = [
  { month: '1月', count: 12 },
  { month: '2月', count: 10 },
  { month: '3月', count: 15 },
  { month: '4月', count: 8 },
  { month: '5月', count: 6 },
  { month: '6月', count: 4 },
]

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('PresidentDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('renders AI monthly summary card', async () => {
    vi.mocked(fetch).mockImplementation((url: string) => {
      if (url.includes('insights')) {
        return Promise.resolve({ json: () => Promise.resolve(mockSummary) })
      }
      if (url.includes('kpi')) {
        return Promise.resolve({ json: () => Promise.resolve(mockKpi) })
      }
      if (url.includes('anomaly-trend')) {
        return Promise.resolve({ json: () => Promise.resolve(mockTrend) })
      }
      return Promise.resolve({ json: () => Promise.resolve({}) })
    })
    renderWithRouter(<PresidentDashboard />)
    expect(await screen.findByText('AI 月报摘要')).toBeInTheDocument()
    expect(await screen.findByText(mockSummary.summary)).toBeInTheDocument()
  })

  it('renders KPI cards with data', async () => {
    vi.mocked(fetch).mockImplementation((url: string) => {
      if (url.includes('insights')) {
        return Promise.resolve({ json: () => Promise.resolve(mockSummary) })
      }
      if (url.includes('kpi')) {
        return Promise.resolve({ json: () => Promise.resolve(mockKpi) })
      }
      if (url.includes('anomaly-trend')) {
        return Promise.resolve({ json: () => Promise.resolve(mockTrend) })
      }
      return Promise.resolve({ json: () => Promise.resolve({}) })
    })
    renderWithRouter(<PresidentDashboard />)
    expect(await screen.findByText('94.2%')).toBeInTheDocument()
    expect(await screen.findByText('1256')).toBeInTheDocument()
    expect(await screen.findByText('18')).toBeInTheDocument()
  })

  it('shows 暂无月报摘要 when no summary data', async () => {
    vi.mocked(fetch).mockImplementation((url: string) => {
      if (url.includes('insights')) {
        return Promise.resolve({ json: () => Promise.resolve({}) })
      }
      if (url.includes('kpi')) {
        return Promise.resolve({ json: () => Promise.resolve(mockKpi) })
      }
      if (url.includes('anomaly-trend')) {
        return Promise.resolve({ json: () => Promise.resolve(mockTrend) })
      }
      return Promise.resolve({ json: () => Promise.resolve({}) })
    })
    renderWithRouter(<PresidentDashboard />)
    expect(await screen.findByText('暂无月报摘要')).toBeInTheDocument()
  })

  it('renders anomaly trend chart', async () => {
    vi.mocked(fetch).mockImplementation((url: string) => {
      if (url.includes('insights')) {
        return Promise.resolve({ json: () => Promise.resolve(mockSummary) })
      }
      if (url.includes('kpi')) {
        return Promise.resolve({ json: () => Promise.resolve(mockKpi) })
      }
      if (url.includes('anomaly-trend')) {
        return Promise.resolve({ json: () => Promise.resolve(mockTrend) })
      }
      return Promise.resolve({ json: () => Promise.resolve({}) })
    })
    renderWithRouter(<PresidentDashboard />)
    expect(await screen.findByText('异常趋势')).toBeInTheDocument()
  })
})
