import React, { useEffect, useState, useCallback } from 'react'
import { Bookmark } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchSavedJobs } from '../../services/jobs'
import { SavedJobItem } from '../../types/job'
import { JobCard } from '../../components/jobs/JobCard'
import { Pagination } from '../../components/jobs/Pagination'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { EmptyState } from '../../components/common/EmptyState'

const PAGE_SIZE = 12

export const SavedJobsPage: React.FC = () => {
  const { token } = useAuth()
  const [savedItems, setSavedItems] = useState<SavedJobItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadSaved = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)

    try {
      const res = await fetchSavedJobs(token, page, PAGE_SIZE)
      setSavedItems(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err: any) {
      setError(err.message || 'Failed to load saved jobs.')
    } finally {
      setIsLoading(false)
    }
  }, [token, page])

  useEffect(() => {
    loadSaved()
  }, [loadSaved])

  const handleSaveToggle = (jobId: string, isSaved: boolean) => {
    if (!isSaved) {
      // Job was unsaved; remove from list
      setSavedItems((prev) => prev.filter((item) => item.job_id !== jobId))
      setTotal((prev) => Math.max(0, prev - 1))
    }
  }

  return (
    <div className="saved-jobs-page">
      <header className="page-header-simple">
        <div className="title-group">
          <div className="icon-badge">
            <Bookmark size={20} className="text-accent" />
          </div>
          <div>
            <h1 className="page-title">Saved Opportunities</h1>
            <p className="page-subtitle">
              Jobs you've bookmarked to review or apply to externally.
            </p>
          </div>
        </div>
      </header>

      {isLoading && <LoadingSkeleton count={3} type="card" />}

      {error && <ErrorMessage message={error} onRetry={loadSaved} />}

      {!isLoading && !error && savedItems.length === 0 && (
        <EmptyState
          title="You haven't saved any jobs yet"
          description="Bookmark interesting job postings while exploring opportunities to keep track of them here."
          actionLabel="Explore Recommended Jobs"
          onAction={() => (window.location.href = '/jobs')}
        />
      )}

      {!isLoading && !error && savedItems.length > 0 && (
        <>
          <div className="saved-jobs-grid">
            {savedItems.map((item) => (
              <JobCard
                key={item.id}
                job={{
                  ...item.job,
                  is_saved: true,
                }}
                onSaveToggle={handleSaveToggle}
              />
            ))}
          </div>

          <Pagination
            currentPage={page}
            totalPages={totalPages}
            totalItems={total}
            pageSize={PAGE_SIZE}
            onPageChange={(newPage) => {
              setPage(newPage)
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          />
        </>
      )}
    </div>
  )
}
