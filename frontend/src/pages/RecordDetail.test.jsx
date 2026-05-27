import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import RecordDetail from './RecordDetail'
import api, { getEmission, getEmissionIssues, getEmissionAudits } from '../api/client'

vi.mock('../api/client', () => ({
  default: { post: vi.fn() },
  getEmission: vi.fn(),
  getEmissionIssues: vi.fn(),
  getEmissionAudits: vi.fn(),
}))

describe('RecordDetail Page', () => {
  const mockRecord = {
    id: 1, source_type: 'SAP', approval_status: 'pending', locked: false,
    co2e_value: '100', record_date: '2023-01-01', organization_name: 'Org A',
    activity_type: 'Diesel'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderComponent = () => render(
    <MemoryRouter initialEntries={['/record/1']}>
      <Routes>
        <Route path="/record/:id" element={<RecordDetail />} />
      </Routes>
    </MemoryRouter>
  )

  it('shows loading state initially', () => {
    getEmission.mockReturnValue(new Promise(() => {}))
    getEmissionIssues.mockReturnValue(new Promise(() => {}))
    getEmissionAudits.mockReturnValue(new Promise(() => {}))
    
    renderComponent()
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('renders record data and approval buttons', async () => {
    getEmission.mockResolvedValue(mockRecord)
    getEmissionIssues.mockResolvedValue({ results: [] })
    getEmissionAudits.mockResolvedValue({ results: [] })
    
    renderComponent()
    
    await waitFor(() => {
      expect(screen.getByText('Org A')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Diesel')).toBeInTheDocument()
    const approveBtn = screen.getByText('Approve')
    const rejectBtn = screen.getByText('Reject')
    
    expect(approveBtn).not.toBeDisabled()
    expect(rejectBtn).not.toBeDisabled()
  })

  it('handles approve action', async () => {
    getEmission.mockResolvedValue(mockRecord)
    getEmissionIssues.mockResolvedValue({ results: [] })
    getEmissionAudits.mockResolvedValue({ results: [] })
    api.post.mockResolvedValue({ data: {} })
    
    renderComponent()
    await waitFor(() => expect(screen.getByText('Org A')).toBeInTheDocument())
    
    const approveBtn = screen.getByText('Approve')
    fireEvent.click(approveBtn)
    
    expect(api.post).toHaveBeenCalledWith('/api/emissions/1/approve/')
    
    await waitFor(() => {
      expect(screen.getByText('Record successfully approved.')).toBeInTheDocument()
    })
  })
})
