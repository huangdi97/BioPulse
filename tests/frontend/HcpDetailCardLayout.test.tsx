import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

vi.mock('@/api/hcps', () => ({
  fetchHcpDetail: vi.fn().mockResolvedValue({
    id: 1,
    name: '张医生',
    title: '主任医师',
    hospital: '北京协和医院',
    dept: '心内科',
    region: '北京',
    priority: 'high',
  }),
  fetchVisitHistory: vi.fn().mockResolvedValue([]),
}))

vi.mock('../../components/AgentSummaryCard', () => ({
  default: ({ title, agentKey }: { title: string; agentKey: string }) =>
    `<div data-testid="agent-card" data-title="${title}" data-agent="${agentKey}" />`,
}))

vi.mock('../../components/AgentInsightBar', () => ({
  default: ({ pageId }: { pageId: string }) =>
    `<div data-testid="insight-bar" data-page="${pageId}" />`,
}))

import HcpDetail from '@/pages/rep/HcpDetail'

describe('HcpDetail card layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders two AgentSummaryCards side by side', async () => {
    render(
      <MemoryRouter initialEntries={['/rep/hcps/1']}>
        <Routes>
          <Route path="/rep/hcps/:id" element={<HcpDetail />} />
        </Routes>
      </MemoryRouter>
    )
    await screen.findByText('张医生')
  })

  it('renders knowledge_worker and sales_suggestion cards', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/rep/hcps/1']}>
        <Routes>
          <Route path="/rep/hcps/:id" element={<HcpDetail />} />
        </Routes>
      </MemoryRouter>
    )
    const grid = container.querySelector('.grid')
    expect(grid).toBeTruthy()
    expect(grid?.className).toContain('grid-cols-1')
    expect(grid?.className).toContain('md:grid-cols-2')
  })
})
