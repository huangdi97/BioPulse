import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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

import client from '@/api/client'
import BiddingMonitor from '@/pages/market/BiddingMonitor'

const mockBiddingData = {
  items: [
    {
      id: 1,
      title: '抗生素招标项目',
      hospital: '北京协和医院',
      product_category: '抗生素',
      budget: 500000,
      publish_date: '2026-06-01',
      deadline: '2026-06-30',
      status: 'preparing',
      created_at: '2026-05-01',
    },
    {
      id: 2,
      title: '抗癌药采购',
      hospital: '上海瑞金医院',
      product_category: '抗癌药',
      budget: 1200000,
      publish_date: '2026-06-15',
      deadline: '2026-07-15',
      status: 'submitted',
      created_at: '2026-05-15',
    },
  ],
}

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('BiddingMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    vi.mocked(client.get).mockResolvedValue({ data: null })
    renderWithRouter(<BiddingMonitor />)
    expect(screen.getByText('招标价格监控')).toBeInTheDocument()
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('renders bidding data after loading', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: mockBiddingData })
    renderWithRouter(<BiddingMonitor />)
    expect(await screen.findByText('抗生素招标项目')).toBeInTheDocument()
    expect(await screen.findByText('抗癌药采购')).toBeInTheDocument()
    expect(screen.getByText('北京协和医院')).toBeInTheDocument()
  })

  it('shows empty state when no data', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: { items: [] } })
    renderWithRouter(<BiddingMonitor />)
    expect(await screen.findByText('暂无招标数据')).toBeInTheDocument()
  })

  it('filters by product name', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: mockBiddingData })
    renderWithRouter(<BiddingMonitor />)
    expect(await screen.findByText('抗生素招标项目')).toBeInTheDocument()

    const input = screen.getByPlaceholderText('产品名搜索...')
    fireEvent.change(input, { target: { value: '抗癌' } })

    expect(screen.queryByText('抗生素招标项目')).not.toBeInTheDocument()
    expect(screen.getByText('抗癌药采购')).toBeInTheDocument()
  })

  it('filters by date range', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: mockBiddingData })
    renderWithRouter(<BiddingMonitor />)
    expect(await screen.findByText('抗生素招标项目')).toBeInTheDocument()

    const dateInputs = screen.getAllByDisplayValue('')
    if (dateInputs.length >= 2) {
      fireEvent.change(dateInputs[0], { target: { value: '2026-06-15' } })
    }

    expect(screen.queryByText('抗生素招标项目')).not.toBeInTheDocument()
  })

  it('handles API error gracefully', async () => {
    vi.mocked(client.get).mockRejectedValue(new Error('Network error'))
    renderWithRouter(<BiddingMonitor />)
    expect(await screen.findByText('暂无招标数据')).toBeInTheDocument()
  })
})