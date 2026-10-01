import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { JobCard } from '../components/jobs/JobCard'
import { JobCard as JobCardType } from '../types/job'
import { AuthProvider } from '../context/AuthContext'

const mockJob: JobCardType = {
  id: '7b7b1234-5678-4321-8765-123456789abc',
  company_id: '11111111-2222-3333-4444-555555555555',
  company_name: 'Stripe',
  company_slug: 'stripe',
  career_source_name: 'Greenhouse',
  title: 'Staff Infrastructure Engineer',
  location: 'San Francisco, CA',
  employment_type: 'full_time',
  workplace_type: 'remote',
  application_url: 'https://boards.greenhouse.io/stripe/jobs/12345',
  first_seen_at: '2026-09-01T12:00:00Z',
  posted_at: '2026-09-01T10:00:00Z',
  canonical_job_id: '7b7b1234-5678-4321-8765-123456789abc',
  is_active: true,
  match_score: 93,
  match_confidence: 'HIGH',
  match_reasons: ['React proficiency aligns', 'Remote preference matches'],
  is_saved: false,
}

describe('JobCard Component', () => {
  it('renders job title, company, location, and match score badge', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <JobCard job={mockJob} />
        </BrowserRouter>
      </AuthProvider>,
    )

    expect(screen.getByText('Staff Infrastructure Engineer')).toBeInTheDocument()
    expect(screen.getByText('Stripe')).toBeInTheDocument()
    expect(screen.getByText('San Francisco, CA')).toBeInTheDocument()
    expect(screen.getByText('remote')).toBeInTheDocument()
    expect(screen.getByText('93%')).toBeInTheDocument()
  })

  it('displays canonical indicator when job is canonical', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <JobCard job={mockJob} />
        </BrowserRouter>
      </AuthProvider>,
    )

    expect(screen.getByText('Canonical')).toBeInTheDocument()
  })

  it('renders external application button with correct link and attributes', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <JobCard job={mockJob} />
        </BrowserRouter>
      </AuthProvider>,
    )

    const applyLink = screen.getByRole('link', { name: /Apply Externally/i })
    expect(applyLink).toBeInTheDocument()
    expect(applyLink).toHaveAttribute('href', mockJob.application_url)
    expect(applyLink).toHaveAttribute('target', '_blank')
    expect(applyLink).toHaveAttribute('rel', 'noopener noreferrer')
  })
})
