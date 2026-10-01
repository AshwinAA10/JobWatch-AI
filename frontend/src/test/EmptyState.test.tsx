import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { EmptyState } from '../components/common/EmptyState'

describe('EmptyState Component', () => {
  it('renders custom title and description', () => {
    render(
      <EmptyState
        title="No matching jobs yet"
        description="We are actively monitoring career portals."
      />,
    )

    expect(screen.getByText('No matching jobs yet')).toBeInTheDocument()
    expect(screen.getByText('We are actively monitoring career portals.')).toBeInTheDocument()
  })

  it('renders and invokes action button when specified', () => {
    const handleAction = vi.fn()
    render(
      <EmptyState
        title="No saved jobs"
        actionLabel="Explore Jobs"
        onAction={handleAction}
      />,
    )

    const btn = screen.getByRole('button', { name: /Explore Jobs/i })
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })
})
