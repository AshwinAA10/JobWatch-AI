import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bookmark,
  Building2,
  MapPin,
  Briefcase,
  ExternalLink,
  Layers,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react'
import { JobCard as JobCardType } from '../../types/job'
import { MatchScoreBadge } from '../matching/MatchScoreBadge'
import { saveJob, unsaveJob } from '../../services/jobs'
import { useAuth } from '../../context/AuthContext'

interface JobCardProps {
  job: JobCardType
  onSaveToggle?: (jobId: string, isSaved: boolean) => void
}

export const JobCard: React.FC<JobCardProps> = ({ job, onSaveToggle }) => {
  const { token, isAuthenticated } = useAuth()
  const [isSaved, setIsSaved] = useState<boolean>(job.is_saved)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const handleToggleSave = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (!isAuthenticated || !token) {
      setSaveError('Please sign in to bookmark jobs.')
      return
    }

    const previousState = isSaved
    const nextState = !previousState

    // Optimistic UI update
    setIsSaved(nextState)
    setIsSaving(true)
    setSaveError(null)

    try {
      if (nextState) {
        await saveJob(job.id, token)
      } else {
        await unsaveJob(job.id, token)
      }
      if (onSaveToggle) {
        onSaveToggle(job.id, nextState)
      }
    } catch {
      // Revert optimistic update on failure
      setIsSaved(previousState)
      setSaveError('Failed to update bookmark.')
    } finally {
      setIsSaving(false)
    }
  }

  // Format posted date
  const postedDate = job.posted_at
    ? new Date(job.posted_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    : null

  return (
    <article
      className={`job-card ${isSaved ? 'job-card-saved' : ''}`}
      aria-labelledby={`job-title-${job.id}`}
    >
      <div className="job-card-top">
        <div className="job-card-main-info">
          <div className="job-card-company-row">
            <span className="job-card-company">
              <Building2 size={14} className="icon-mr" aria-hidden="true" />
              {job.company_name}
            </span>
            {job.career_source_name && (
              <span className="source-pill" title={`Source: ${job.career_source_name}`}>
                {job.career_source_name}
              </span>
            )}
            {job.canonical_job_id && (
              <span className="canonical-pill" title="Deduplicated canonical job posting">
                <Layers size={11} className="icon-mr" />
                Canonical
              </span>
            )}
          </div>

          <h3 id={`job-title-${job.id}`} className="job-card-title">
            <Link to={`/jobs/${job.id}`} className="job-title-link">
              {job.title}
            </Link>
          </h3>

          <div className="job-meta-row">
            {job.location && (
              <span className="job-meta-item">
                <MapPin size={13} className="icon-mr" aria-hidden="true" />
                {job.location}
              </span>
            )}
            {job.workplace_type && (
              <span className="job-meta-item">
                <Briefcase size={13} className="icon-mr" aria-hidden="true" />
                {job.workplace_type}
              </span>
            )}
            {job.employment_type && (
              <span className="meta-pill">{job.employment_type.replace('_', ' ')}</span>
            )}
            {postedDate && <span className="job-date-text">Posted {postedDate}</span>}
          </div>
        </div>

        <div className="job-card-aside">
          <MatchScoreBadge score={job.match_score} confidence={job.match_confidence} size="md" />

          <button
            type="button"
            className={`btn-icon-save ${isSaved ? 'btn-saved' : ''}`}
            onClick={handleToggleSave}
            disabled={isSaving}
            aria-label={isSaved ? `Unsave ${job.title}` : `Save ${job.title}`}
            title={isSaved ? 'Remove from saved jobs' : 'Save job'}
          >
            <Bookmark size={18} fill={isSaved ? 'currentColor' : 'none'} />
          </button>
        </div>
      </div>

      {/* Match reasons if present */}
      {job.match_reasons && job.match_reasons.length > 0 && (
        <div className="job-reasons-preview">
          <span className="reasons-label">Key Match: </span>
          <span className="reasons-text">{job.match_reasons.slice(0, 2).join(' · ')}</span>
        </div>
      )}

      {saveError && <div className="save-error-hint">{saveError}</div>}

      <div className="job-card-footer">
        <div className="footer-left">
          {job.application_id ? (
            <Link
              to={`/applications/${job.application_id}`}
              className="badge badge-primary flex-center gap-xs text-xs py-xs px-sm hover-underline"
              onClick={(e) => e.stopPropagation()}
            >
              <CheckCircle2 size={12} />
              Applied ({job.application_status || 'Active'})
            </Link>
          ) : (
            job.application_url && (
              <a
                href={job.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary btn-xs"
                onClick={(e) => e.stopPropagation()}
              >
                Apply Externally
                <ExternalLink size={12} className="icon-ml" />
              </a>
            )
          )}
        </div>

        <Link to={`/jobs/${job.id}`} className="btn btn-primary btn-xs">
          View Details
          <ArrowRight size={13} className="icon-ml" />
        </Link>
      </div>
    </article>
  )
}
