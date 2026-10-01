import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AIInsightsCard } from '../components/matching/AIInsightsCard'

describe('AIInsightsCard Component', () => {
  it('renders AI narrative insights when available', () => {
    const aiData = {
      summary: 'Candidate exhibits deep expertise in React and Python.',
      strengths: ['Strong distributed system knowledge', 'Proven cloud background'],
      gaps: ['Limited Kubernetes production experience'],
      recommendation: 'Highly recommended for an interview.',
    }

    render(<AIInsightsCard aiExplanation={aiData} />)

    expect(screen.getByText('AI-Assisted Insights')).toBeInTheDocument()
    expect(screen.getByText(/deep expertise in React and Python/i)).toBeInTheDocument()
    expect(screen.getByText('Strong distributed system knowledge')).toBeInTheDocument()
    expect(screen.getByText('Limited Kubernetes production experience')).toBeInTheDocument()
    expect(screen.getByText(/Highly recommended for an interview/i)).toBeInTheDocument()
  })

  it('renders deterministic fallback explanation when AI explanation is absent', () => {
    const fallback = {
      reasons: ['Skill React matches profile', 'Location San Francisco matches preference'],
    }

    render(<AIInsightsCard aiExplanation={null} deterministicFallback={fallback} />)

    expect(screen.getByText(/Deterministic Match Reasoning/i)).toBeInTheDocument()
    expect(screen.getByText('Skill React matches profile')).toBeInTheDocument()
  })

  it('renders null when neither AI nor fallback is provided', () => {
    const { container } = render(<AIInsightsCard aiExplanation={null} deterministicFallback={{ reasons: [] }} />)
    expect(container).toBeEmptyDOMElement()
  })
})
