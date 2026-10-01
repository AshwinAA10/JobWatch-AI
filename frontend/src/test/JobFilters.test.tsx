import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { JobFilters, FilterState } from '../components/jobs/JobFilters'

describe('JobFilters Component', () => {
  const defaultFilters: FilterState = {
    location: '',
    workplace_type: '',
    employment_type: '',
    min_match: '',
  }

  it('renders filter dropdowns and inputs properly', () => {
    const handleChange = vi.fn()
    const handleReset = vi.fn()

    render(
      <JobFilters
        filters={defaultFilters}
        onChange={handleChange}
        onReset={handleReset}
      />,
    )

    expect(screen.getByLabelText(/Workplace Type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Employment Type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Minimum Match Score/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Location/i)).toBeInTheDocument()
  })

  it('triggers onChange when a filter selection changes', () => {
    const handleChange = vi.fn()
    const handleReset = vi.fn()

    render(
      <JobFilters
        filters={defaultFilters}
        onChange={handleChange}
        onReset={handleReset}
      />,
    )

    const select = screen.getByLabelText(/Workplace Type/i)
    fireEvent.change(select, { target: { value: 'remote' } })

    expect(handleChange).toHaveBeenCalledWith({
      ...defaultFilters,
      workplace_type: 'remote',
    })
  })

  it('shows Reset button when active filters exist and triggers onReset', () => {
    const handleChange = vi.fn()
    const handleReset = vi.fn()

    const activeFilters: FilterState = {
      location: 'New York',
      workplace_type: 'hybrid',
      employment_type: '',
      min_match: '80',
    }

    render(
      <JobFilters
        filters={activeFilters}
        onChange={handleChange}
        onReset={handleReset}
      />,
    )

    const resetBtn = screen.getByRole('button', { name: /Reset/i })
    expect(resetBtn).toBeInTheDocument()

    fireEvent.click(resetBtn)
    expect(handleReset).toHaveBeenCalled()
  })
})
