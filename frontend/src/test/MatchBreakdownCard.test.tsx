import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MatchBreakdownCard } from '../components/matching/MatchBreakdownCard'

describe('MatchBreakdownCard Component', () => {
  it('renders breakdown progress rows with labels and values', () => {
    const breakdown = {
      skills: 95,
      experience: 82,
      location: 100,
      workplace: 90,
      semantic_fit: 89,
    }

    render(<MatchBreakdownCard breakdown={breakdown} />)

    expect(screen.getByText('Skills Match')).toBeInTheDocument()
    expect(screen.getByText('95%')).toBeInTheDocument()

    expect(screen.getByText('Experience Level')).toBeInTheDocument()
    expect(screen.getByText('82%')).toBeInTheDocument()

    expect(screen.getByText('Location Fit')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()

    expect(screen.getByText('Workplace Preference')).toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()

    expect(screen.getByText('Semantic Fit')).toBeInTheDocument()
    expect(screen.getByText('89%')).toBeInTheDocument()
  })

  it('renders graceful fallback message when breakdown is null or empty', () => {
    render(<MatchBreakdownCard breakdown={null} />)
    expect(screen.getByText(/Detailed category breakdown is not available/i)).toBeInTheDocument()
  })
})
