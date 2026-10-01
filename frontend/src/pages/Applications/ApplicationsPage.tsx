import React, { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Briefcase,
  Building2,
  MapPin,
  Calendar,
  Search,
  ArrowRight,
  MessageSquare,
  Video,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchApplications,
  fetchApplicationStats,
} from '../../services/applications'
import {
  ApplicationListItem,
  ApplicationStats,
} from '../../types/application'
import { ApplicationStatusBadge } from '../../components/applications/ApplicationStatusBadge'
import { MatchScoreBadge } from '../../components/matching/MatchScoreBadge'
import { Pagination } from '../../components/jobs/Pagination'

const STATUS_TABS: { label: string; value: string }[] = [
  { label: 'All', value: '' },
  { label: 'Applied', value: 'APPLIED' },
  { label: 'Screening', value: 'SCREENING' },
  { label: 'Interview', value: 'INTERVIEW' },
  { label: 'Offer', value: 'OFFER' },
  { label: 'Accepted', value: 'ACCEPTED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'Withdrawn', value: 'WITHDRAWN' },
]

export const ApplicationsPage: React.FC = () => {
  const { token, isAuthenticated } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const currentStatus = searchParams.get('status') || ''
  const currentQuery = searchParams.get('q') || ''
  const currentSort = (searchParams.get('sort_by') || 'newest') as
    | 'newest'
    | 'oldest'
    | 'recently_updated'
    | 'company'
  const currentPage = parseInt(searchParams.get('page') || '1', 10)

  const [applications, setApplications] = useState<ApplicationListItem[]>([])
  const [stats, setStats] = useState<ApplicationStats | null>(null)
  const [total, setTotal] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(1)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState<string>(currentQuery)

  const loadData = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const [appsRes, statsRes] = await Promise.all([
        fetchApplications(token, {
          status: currentStatus || undefined,
          q: currentQuery || undefined,
          sort_by: currentSort,
          page: currentPage,
          page_size: 12,
        }),
        fetchApplicationStats(token).catch(() => null),
      ])

      setApplications(appsRes.items)
      setTotal(appsRes.total)
      setTotalPages(appsRes.total_pages)
      if (statsRes) setStats(statsRes)
    } catch (err: any) {
      setError(err.message || 'Failed to load tracked applications.')
    } finally {
      setIsLoading(false)
    }
  }, [token, currentStatus, currentQuery, currentSort, currentPage])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Sync search input when URL changes
  useEffect(() => {
    setSearchInput(currentQuery)
  }, [currentQuery])

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) {
      next.set(key, value)
    } else {
      next.delete(key)
    }
    if (key !== 'page') {
      next.set('page', '1')
    }
    setSearchParams(next)
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateParam('q', searchInput.trim())
  }

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return isoString
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="container py-xl text-center">
        <h2 className="heading-lg mb-md">Application Tracking</h2>
        <p className="text-muted mb-lg">
          Please sign in to track and manage your job applications.
        </p>
        <Link to="/login" className="btn btn-primary">
          Sign In
        </Link>
      </div>
    )
  }

  return (
    <div className="container applications-page py-lg" id="applications-page-container">
      {/* Header & Stats Banner */}
      <header className="page-header mb-lg">
        <div className="flex-between flex-wrap gap-md">
          <div>
            <h1 className="heading-xl flex-center gap-sm">
              <Briefcase className="text-primary" size={28} />
              Application Tracking
            </h1>
            <p className="text-muted text-sm mt-xs">
              Manage your active applications, schedule interviews, and track your hiring lifecycle.
            </p>
          </div>
          <Link to="/jobs" className="btn btn-outline btn-sm flex-center gap-xs">
            <Search size={14} />
            Discover More Jobs
          </Link>
        </div>

        {/* Stats strip */}
        {stats && (
          <div className="app-stats-grid mt-lg">
            <div className="stat-card" onClick={() => updateParam('status', '')} role="button" tabIndex={0}>
              <span className="stat-label">Total Applications</span>
              <span className="stat-number">{stats.total}</span>
            </div>
            <div className="stat-card stat-applied" onClick={() => updateParam('status', 'APPLIED')} role="button" tabIndex={0}>
              <span className="stat-label">Applied</span>
              <span className="stat-number text-blue">{stats.applied}</span>
            </div>
            <div className="stat-card stat-interview" onClick={() => updateParam('status', 'INTERVIEW')} role="button" tabIndex={0}>
              <span className="stat-label">Interviews</span>
              <span className="stat-number text-amber">{stats.interview}</span>
            </div>
            <div className="stat-card stat-offer" onClick={() => updateParam('status', 'OFFER')} role="button" tabIndex={0}>
              <span className="stat-label">Offers</span>
              <span className="stat-number text-emerald">{stats.offer}</span>
            </div>
            <div className="stat-card stat-rejected" onClick={() => updateParam('status', 'REJECTED')} role="button" tabIndex={0}>
              <span className="stat-label">Rejected</span>
              <span className="stat-number text-rose">{stats.rejected}</span>
            </div>
          </div>
        )}
      </header>

      {/* Controls & Filter bar */}
      <section className="applications-controls mb-md" aria-label="Application Filters">
        {/* Status Tabs */}
        <div className="status-tabs flex-wrap gap-xs mb-md" role="tablist">
          {STATUS_TABS.map((tab) => {
            const isActive = currentStatus === tab.value
            return (
              <button
                key={tab.value}
                role="tab"
                aria-selected={isActive}
                className={`tab-btn ${isActive ? 'tab-btn-active' : ''}`}
                onClick={() => updateParam('status', tab.value)}
              >
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Search & Sort */}
        <div className="search-sort-bar flex-between flex-wrap gap-sm">
          <form onSubmit={handleSearchSubmit} className="search-form flex-1 min-w-xs">
            <div className="search-input-wrapper">
              <Search size={16} className="search-icon text-muted" />
              <input
                type="text"
                className="form-control form-control-search"
                placeholder="Search applications by role, company, or location..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
          </form>

          <div className="sort-wrapper flex-center gap-xs">
            <span className="text-xs text-muted">Sort:</span>
            <select
              className="form-control form-control-sm select-auto"
              value={currentSort}
              onChange={(e) => updateParam('sort_by', e.target.value)}
              aria-label="Sort applications"
            >
              <option value="newest">Recently Applied</option>
              <option value="recently_updated">Recently Updated</option>
              <option value="company">Company (A-Z)</option>
              <option value="oldest">Oldest</option>
            </select>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      {error && (
        <div className="alert alert-error mb-lg" role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="loading-state text-center py-xl">
          <Loader2 size={32} className="spinner text-primary mx-auto mb-sm" />
          <p className="text-muted">Loading your tracked applications...</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="empty-state card text-center py-xl my-lg">
          <Briefcase size={40} className="text-muted mx-auto mb-md" />
          <h3 className="heading-md mb-xs">No Applications Found</h3>
          <p className="text-muted text-sm max-w-sm mx-auto mb-lg">
            {currentStatus || currentQuery
              ? 'No applications match your active filters or search keyword.'
              : "You haven't tracked any job applications yet. When you discover jobs and apply externally, mark them as applied to track their status."}
          </p>
          {currentStatus || currentQuery ? (
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => {
                setSearchParams(new URLSearchParams())
                setSearchInput('')
              }}
            >
              Clear Filters
            </button>
          ) : (
            <Link to="/jobs" className="btn btn-primary btn-sm">
              Discover Jobs to Apply
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="applications-list grid-list gap-md">
            {applications.map((app) => (
              <article key={app.id} className="application-card card hover-card">
                <div className="card-top flex-between flex-wrap gap-sm">
                  <div className="role-company">
                    <h3 className="app-role-title">
                      <Link to={`/applications/${app.id}`} className="hover-underline">
                        {app.job_title}
                      </Link>
                    </h3>
                    <div className="app-company-meta flex-center gap-xs text-muted text-sm mt-xs">
                      <Building2 size={14} />
                      <span className="font-medium text-main">{app.company_name}</span>
                      {app.job_location && (
                        <>
                          <span className="meta-dot">·</span>
                          <MapPin size={13} />
                          <span>{app.job_location}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="status-score-aside flex-center gap-sm">
                    {app.match_score_at_application !== null && app.match_score_at_application !== undefined && (
                      <MatchScoreBadge score={app.match_score_at_application} size="sm" />
                    )}
                    <ApplicationStatusBadge status={app.status} size="md" />
                  </div>
                </div>

                <div className="card-middle flex-between flex-wrap gap-sm mt-md pt-sm border-t">
                  <div className="dates-meta text-xs text-muted flex-center gap-md">
                    <span className="flex-center gap-xs">
                      <Calendar size={13} />
                      Applied: {formatDate(app.applied_at)}
                    </span>
                    <span className="text-subtle">
                      Updated: {formatDate(app.last_status_changed_at)}
                    </span>
                  </div>

                  <div className="activity-counters flex-center gap-md text-xs text-muted">
                    {app.interviews_count > 0 && (
                      <span className="flex-center gap-xs text-amber font-medium">
                        <Video size={13} />
                        {app.interviews_count} Interview{app.interviews_count > 1 ? 's' : ''}
                      </span>
                    )}
                    {app.notes_count > 0 && (
                      <span className="flex-center gap-xs">
                        <MessageSquare size={13} />
                        {app.notes_count} Note{app.notes_count > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>

                <div className="card-footer flex-between gap-sm mt-sm">
                  <div>
                    {app.job_id && (
                      <Link
                        to={`/jobs/${app.job_id}`}
                        className="btn btn-ghost btn-xs text-muted"
                        title="View job posting"
                      >
                        View Job
                      </Link>
                    )}
                  </div>

                  <Link
                    to={`/applications/${app.id}`}
                    className="btn btn-outline btn-xs flex-center gap-xs"
                  >
                    Manage Lifecycle
                    <ArrowRight size={13} />
                  </Link>
                </div>
              </article>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-xl flex-center">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={total}
                pageSize={12}
                onPageChange={(page) => updateParam('page', page.toString())}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
