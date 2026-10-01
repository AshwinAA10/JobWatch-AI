import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MatchScoreBadge } from '../components/matching/MatchScoreBadge'

describe('MatchScoreBadge Component', () => {
  it('renders percentage score accurately for 91%', () => {
    render(<MatchScoreBadge score={91} />)
    expect(screen.getByText('91%')).toBeInTheDocument()
    expect(screen.getByText('Strong Fit')).toBeInTheDocument()
  })

  it('renders moderate fit tier for score of 68%', () => {
    render(<MatchScoreBadge score={68} />)
    expect(screen.getByText('68%')).toBeInTheDocument()
    expect(screen.getByText('Moderate Fit')).toBeInTheDocument()
  })

  it('renders low fit tier for score of 42%', () => {
    render(<MatchScoreBadge score={42} />)
    expect(screen.getByText('42%')).toBeInTheDocument()
    expect(screen.getByText('Low Fit')).toBeInTheDocument()
  })

  it('gracefully renders "Unscored" when score is null or undefined', () => {
    render(<MatchScoreBadge score={null} />)
    expect(screen.getByText('Unscored')).toBeInTheDocument()
  })

  it('displays confidence level when provided', () => {
    render(<MatchScoreBadge score={85} confidence="HIGH" />)
    expect(screen.getByText(/Strong Fit \(high\)/i)).toBeInTheDocument()
  })
})
