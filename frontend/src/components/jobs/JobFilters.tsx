import React from 'react'
import { Filter, X, RotateCcw } from 'lucide-react'

export interface FilterState {
  location: string
  workplace_type: string
  employment_type: string
  min_match: string
}

interface JobFiltersProps {
  filters: FilterState
  onChange: (filters: FilterState) => void
  onReset: () => void
  isOpenMobile?: boolean
  onCloseMobile?: () => void
}

export const JobFilters: React.FC<JobFiltersProps> = ({
  filters,
  onChange,
  onReset,
  isOpenMobile = false,
  onCloseMobile,
}) => {
  const handleChange = (field: keyof FilterState, value: string) => {
    onChange({
      ...filters,
      [field]: value,
    })
  }

  const hasActiveFilters = Boolean(
    filters.location ||
    filters.workplace_type ||
    filters.employment_type ||
    filters.min_match
  )

  const content = (
    <div className="filters-container">
      <div className="filters-header">
        <div className="filters-title-group">
          <Filter size={18} className="icon-mr" />
          <h3 className="filters-title">Filter Opportunities</h3>
        </div>
        {hasActiveFilters && (
          <button
            type="button"
            className="btn-link btn-xs"
            onClick={onReset}
            title="Reset all filters"
          >
            <RotateCcw size={12} className="icon-mr" />
            Reset
          </button>
        )}
      </div>

      {/* Workplace Type */}
      <div className="filter-group">
        <label htmlFor="filter-workplace" className="filter-label">
          Workplace Type
        </label>
        <select
          id="filter-workplace"
          className="form-select"
          value={filters.workplace_type}
          onChange={(e) => handleChange('workplace_type', e.target.value)}
        >
          <option value="">All Workplace Types</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">On-Site</option>
        </select>
      </div>

      {/* Employment Type */}
      <div className="filter-group">
        <label htmlFor="filter-employment" className="filter-label">
          Employment Type
        </label>
        <select
          id="filter-employment"
          className="form-select"
          value={filters.employment_type}
          onChange={(e) => handleChange('employment_type', e.target.value)}
        >
          <option value="">All Types</option>
          <option value="full_time">Full-Time</option>
          <option value="part_time">Part-Time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
        </select>
      </div>

      {/* Minimum Match Score */}
      <div className="filter-group">
        <label htmlFor="filter-min-match" className="filter-label">
          Minimum Match Score
        </label>
        <select
          id="filter-min-match"
          className="form-select"
          value={filters.min_match}
          onChange={(e) => handleChange('min_match', e.target.value)}
        >
          <option value="">Any Match Score</option>
          <option value="90">90%+ (Exceptional Fit)</option>
          <option value="80">80%+ (Strong Fit)</option>
          <option value="70">70%+ (Good Fit)</option>
          <option value="50">50%+ (Moderate Fit)</option>
        </select>
      </div>

      {/* Location */}
      <div className="filter-group">
        <label htmlFor="filter-location" className="filter-label">
          Location
        </label>
        <input
          id="filter-location"
          type="text"
          className="form-input"
          placeholder="e.g. San Francisco, NY, Remote"
          value={filters.location}
          onChange={(e) => handleChange('location', e.target.value)}
        />
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Filter Sidebar */}
      <aside className="filters-sidebar desktop-only" aria-label="Job filters">
        {content}
      </aside>

      {/* Mobile Drawer */}
      {isOpenMobile && (
        <div className="filters-drawer-overlay mobile-only" onClick={onCloseMobile}>
          <div
            className="filters-drawer-panel"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Filter Jobs"
          >
            <div className="drawer-header">
              <h4>Filter Jobs</h4>
              <button
                type="button"
                className="btn-icon"
                onClick={onCloseMobile}
                aria-label="Close filters"
              >
                <X size={20} />
              </button>
            </div>
            <div className="drawer-body">{content}</div>
            <div className="drawer-footer">
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={onCloseMobile}
              >
                Show Results
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
