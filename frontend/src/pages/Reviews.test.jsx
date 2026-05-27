import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Reviews from './Reviews'
import * as client from '../api/client'

vi.mock('../api/client', () => ({
  getEmissions: vi.fn(),
  getValidationIssues: vi.fn(),
}))

describe('Reviews Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders records after loading', async () => {
    client.getEmissions.mockResolvedValueOnce({
      results: [
        { id: 1, source_type: 'SAP', approval_status: 'pending', co2e_value: '100', record_date: '2023-01-01' }
      ],
      count: 1
    })
    client.getValidationIssues.mockResolvedValueOnce({ results: [] })
    
    render(<MemoryRouter><Reviews /></MemoryRouter>)
    
    await waitFor(() => {
      expect(screen.getByText('SAP')).toBeInTheDocument()
    })
    expect(screen.getByText('pending')).toBeInTheDocument()
  })
})
