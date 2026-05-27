import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import Uploads from './Uploads'

vi.mock('../api/client', () => ({
  uploadSAP: vi.fn(),
  uploadUtility: vi.fn(),
  uploadTravel: vi.fn(),
}))

describe('Uploads Page', () => {
  it('renders Uploads page with 3 sections', () => {
    render(<MemoryRouter><Uploads /></MemoryRouter>)
    expect(screen.getByText('SAP Data Upload')).toBeInTheDocument()
    expect(screen.getByText('Utility Data Upload')).toBeInTheDocument()
    expect(screen.getByText('Travel Data Upload')).toBeInTheDocument()
  })
})
