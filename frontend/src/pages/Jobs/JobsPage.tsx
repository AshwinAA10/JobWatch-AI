import React, { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Filter, SlidersHorizontal } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchJobs } from '../../services/jobs'
import { JobCard as JobCardType } from '../../types/job'
import { JobCard } from '../../components/jobs/JobCard'
import { SearchBar } from '../../components/jobs/SearchBar'
import { JobFilters, FilterState } from '../../components/jobs/JobFilters'
import { Pagination } from '../../components/jobs/Pagination'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { EmptyState } from '../../components/common/EmptyState'

const PAGE_SIZE = 12

export const JobsPage: React.FC = () => {
  const { token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  // Read URL query params
  const q = searchParams.get('q') || ''
  const location = searchParams.get('location') || ''
  const workplaceType = searchParams.get('workplace_type') || ''
  const employmentType = searchParams.get('employment_type') || ''
  const minMatch = searchParams.get('min_match') || ''
  const sortBy = (searchParams.get('sort_by') as 'best_match' | 'newest' | 'title') || 'best_match'
  const page = parseInt(searchParams.get('page') || '1', 10)

  const [jobs, setJobs] = useState<JobCardType[]>([])
  const [total, setTotal] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState<boolean>(false)

  // Sync state to URL
  const updateURLParams = useCallback(
    (newParams: Record<string, string | number | null | undefined>) => {
      const updated = new URLSearchParams(searchParams)
      Object.entries(newParams).forEach(([key, value]) => {
        if (value === null || value === undefined || value === '' || value === 0) {
          updated.delete(key)
        } else {
          updated.set(key, value.toString())
        }
      })
      setSearchParams(updated)
    },
    [searchParams, setSearchParams],
  )

  const loadJobs = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const minScoreNum = minMatch ? parseFloat(minMatch) : undefined
      const res = await fetchJobs(
        {
          q: q || undefined,
          location: location || undefined,
          workplace_type: workplaceType || undefined,
          employment_type: employmentType || undefined,
          min_score: minScoreNum,
          sort_by: sortBy,
          page,
          page_size: PAGE_SIZE,
        },
        token,
      )

      setJobs(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job postings.')
    } finally {
      setIsLoading(false)
    }
  }, [q, location, workplaceType, employmentType, minMatch, sortBy, page, token])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const handleSearchChange = (newQ: string) => {
    updateURLParams({ q: newQ, page: 1 })
  }

  const handleFilterChange = (newFilters: FilterState) => {
    updateURLParams({
      location: newFilters.location,
      workplace_type: newFilters.workplace_type,
      employment_type: newFilters.employment_type,
      min_match: newFilters.min_match,
      page: 1,
    })
  }

  const handleResetFilters = () => {
    updateURLParams({
      location: null,
      workplace_type: null,
      employment_type: null,
      min_match: null,
      page: 1,
    })
  }

  const handleSortChange = (newSort: string) => {
    updateURLParams({ sort_by: newSort, page: 1 })
  }

  const handlePageChange = (newPage: number) => {
    updateURLParams({ page: newPage })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const activeFiltersCount = [location, workplaceType, employmentType, minMatch].filter(Boolean).length

  return (
    <div className="jobs-page-layout">
      {/* Top search & sorting toolbar */}
      <div className="jobs-toolbar">
        <div className="toolbar-search-col">
          <SearchBar value={q} onChange={handleSearchChange} />
        </div>

        <div className="toolbar-controls-col">
          {/* Mobile Filter Button */}
          <button
            type="button"
            className="btn btn-secondary mobile-only filter-trigger-btn"
            onClick={() => setIsMobileFilterOpen(true)}
            aria-label="Open filter options"
          >
            <Filter size={16} className="icon-mr" />
            <span>Filters</span>
            {activeFiltersCount > 0 && (
              <span className="badge badge-accent ml-1">{activeFiltersCount}</span>
            )}
          </button>

          {/* Sort Selector */}
          <div className="sort-control-group">
            <SlidersHorizontal size={14} className="sort-icon desktop-only" aria-hidden="true" />
            <label htmlFor="sort-select" className="sr-only">
              Sort jobs by
            </label>
            <select
              id="sort-select"
              className="form-select form-select-sm"
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
            >
              <option value="best_match">Sort: Best Match</option>
              <option value="newest">Sort: Newest</option>
              <option value="title">Sort: Job Title</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content: Sidebar Filters + Jobs Grid */}
      <div className="jobs-split-container">
        {/* Filter Sidebar & Drawer */}
        <JobFilters
          filters={{
            location,
            workplace_type: workplaceType,
            employment_type: employmentType,
            min_match: minMatch,
          }}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
          isOpenMobile={isMobileFilterOpen}
          onCloseMobile={() => setIsMobileFilterOpen(false)}
        />

        {/* Jobs List Area */}
        <main className="jobs-list-area">
          <div className="jobs-results-header">
            <h2 className="results-count-text">
              {isLoading ? (
                'Searching opportunities...'
              ) : (
                <>
                  Found <span className="text-strong">{total}</span> career opportunities
                </>
              )}
            </h2>
          </div>

          {isLoading && <LoadingSkeleton count={4} type="card" />}

          {error && <ErrorMessage message={error} onRetry={loadJobs} />}

          {!isLoading && !error && jobs.length === 0 && (
            <EmptyState
              title="No jobs found matching your criteria"
              description="Try adjusting your keywords, location, or lowering the minimum match threshold."
              actionLabel="Clear Filters"
              onAction={handleResetFilters}
            />
          )}

          {!isLoading && !error && jobs.length > 0 && (
            <>
              <div className="jobs-grid">
                {jobs.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>

              <Pagination
                currentPage={page}
                totalPages={totalPages}
                totalItems={total}
                pageSize={PAGE_SIZE}
                onPageChange={handlePageChange}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}
