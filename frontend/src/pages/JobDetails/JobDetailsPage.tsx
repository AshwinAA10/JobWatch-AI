import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import DOMPurify from 'dompurify'
import {
  Building2,
  MapPin,
  Briefcase,
  Calendar,
  ExternalLink,
  Bookmark,
  ArrowLeft,
  ArrowRight,
  Layers,
  FileText,
  CheckCircle2,
  Loader2,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchJobDetail, saveJob, unsaveJob } from '../../services/jobs'
import { createApplication } from '../../services/applications'
import { JobDetail } from '../../types/job'
import { MatchScoreBadge } from '../../components/matching/MatchScoreBadge'
import { MatchBreakdownCard } from '../../components/matching/MatchBreakdownCard'
import { MatchExplanationCard } from '../../components/matching/MatchExplanationCard'
import { AIInsightsCard } from '../../components/matching/AIInsightsCard'
import { SkillGapCard } from '../../components/matching/SkillGapCard'
import { ApplicationStatusBadge } from '../../components/applications/ApplicationStatusBadge'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'

export const JobDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { token, isAuthenticated } = useAuth()

  const [job, setJob] = useState<JobDetail | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const [isSaved, setIsSaved] = useState<boolean>(false)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [applicationId, setApplicationId] = useState<string | null>(null)
  const [applicationStatus, setApplicationStatus] = useState<string | null>(null)
  const [isApplying, setIsApplying] = useState<boolean>(false)
  const [applyError, setApplyError] = useState<string | null>(null)

  const loadJob = async () => {
    if (!id) return
    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchJobDetail(id, token)
      setJob(data)
      setIsSaved(data.is_saved)
      setApplicationId(data.application_id || null)
      setApplicationStatus(data.application_status || null)
    } catch (err: any) {
      setError(err.message || 'Failed to load job details.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleMarkAsApplied = async () => {
    if (!isAuthenticated || !token || !job) {
      return
    }

    setIsApplying(true)
    setApplyError(null)

    try {
      const app = await createApplication(token, {
        job_id: job.id,
        external_application_url: job.application_url || undefined,
      })
      setApplicationId(app.id)
      setApplicationStatus(app.status)
    } catch (err: any) {
      setApplyError(err.message || 'Failed to mark as applied.')
    } finally {
      setIsApplying(false)
    }
  }

  useEffect(() => {
    loadJob()
  }, [id, token])

  const handleToggleSave = async () => {
    if (!job) return
    if (!isAuthenticated || !token) {
      setSaveError('Please sign in to save opportunities.')
      return
    }

    const previousState = isSaved
    const nextState = !previousState

    setIsSaved(nextState)
    setIsSaving(true)
    setSaveError(null)

    try {
      if (nextState) {
        await saveJob(job.id, token)
      } else {
        await unsaveJob(job.id, token)
      }
    } catch {
      setIsSaved(previousState)
      setSaveError('Could not update saved status.')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="job-details-loading-view">
        <LoadingSkeleton count={2} type="detail" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="job-details-error-view">
        <ErrorMessage
          title="Unable to load job posting"
          message={error || 'Job not found.'}
          onRetry={loadJob}
        />
        <div className="mt-3">
          <Link to="/jobs" className="btn btn-secondary btn-sm">
            <ArrowLeft size={14} className="icon-mr" />
            Back to Job Discovery
          </Link>
        </div>
      </div>
    )
  }

  // Format posted date
  const postedDate = job.posted_at
    ? new Date(job.posted_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  // Sanitize description with DOMPurify
  const sanitizedDescription = job.description
    ? DOMPurify.sanitize(job.description, {
        ALLOWED_TAGS: [
          'p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'span', 'blockquote', 'code', 'pre'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
      })
    : null

  const reqs = job.structured_requirements

  return (
    <div className="job-details-page">
      {/* Navigation breadcrumb */}
      <div className="breadcrumb-nav">
        <Link to="/jobs" className="breadcrumb-link">
          <ArrowLeft size={15} className="icon-mr" />
          Back to Jobs
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{job.title}</span>
      </div>

      {/* Main Header Card */}
      <header className="job-header-card">
        <div className="header-top-split">
          <div className="header-info-main">
            <div className="header-company-badges">
              <span className="header-company">
                <Building2 size={16} className="icon-mr" aria-hidden="true" />
                {job.company_name}
              </span>
              {job.career_source_name && (
                <span className="source-pill">Source: {job.career_source_name}</span>
              )}
              {job.duplicate_count > 0 && (
                <span
                  className="canonical-pill"
                  title={`Deduplicated across ${job.duplicate_count + 1} postings`}
                >
                  <Layers size={13} className="icon-mr" />
                  Canonical Posting (+{job.duplicate_count} duplicate{job.duplicate_count > 1 ? 's' : ''})
                </span>
              )}
            </div>

            <h1 className="job-details-title">{job.title}</h1>

            <div className="job-meta-chips">
              {job.location && (
                <span className="meta-chip">
                  <MapPin size={14} className="icon-mr text-accent" />
                  {job.location}
                </span>
              )}
              {job.workplace_type && (
                <span className="meta-chip">
                  <Briefcase size={14} className="icon-mr text-accent" />
                  {job.workplace_type}
                </span>
              )}
              {job.employment_type && (
                <span className="meta-chip">{job.employment_type.replace('_', ' ')}</span>
              )}
              {postedDate && (
                <span className="meta-chip">
                  <Calendar size={14} className="icon-mr text-muted" />
                  Posted {postedDate}
                </span>
              )}
            </div>
          </div>

          {/* Match Score & Action CTA */}
          <div className="header-action-aside">
            <div className="header-score-box">
              <span className="score-box-label">Candidate Fit</span>
              <MatchScoreBadge score={job.match_score} confidence={job.match_confidence} size="lg" />
            </div>

            <div className="action-buttons-group">
              {applicationId ? (
                <div className="application-tracking-status-box flex-center flex-wrap gap-xs">
                  <ApplicationStatusBadge status={applicationStatus || 'APPLIED'} size="md" />
                  <Link
                    to={`/applications/${applicationId}`}
                    className="btn btn-primary btn-sm flex-center gap-xs"
                  >
                    View Application <ArrowRight size={14} />
                  </Link>
                </div>
              ) : (
                <>
                  {job.application_url && (
                    <a
                      href={job.application_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary btn-apply"
                    >
                      Apply Externally
                      <ExternalLink size={15} className="icon-ml" />
                    </a>
                  )}

                  {isAuthenticated && (
                    <button
                      type="button"
                      className="btn btn-outline btn-sm flex-center gap-xs"
                      onClick={handleMarkAsApplied}
                      disabled={isApplying}
                      title="Track this job in your applications"
                    >
                      {isApplying ? (
                        <Loader2 size={14} className="spinner" />
                      ) : (
                        <CheckCircle2 size={14} className="text-primary" />
                      )}
                      Mark as Applied
                    </button>
                  )}
                </>
              )}

              <button
                type="button"
                className={`btn btn-secondary ${isSaved ? 'btn-saved-active' : ''}`}
                onClick={handleToggleSave}
                disabled={isSaving}
                aria-label={isSaved ? 'Remove from saved' : 'Save opportunity'}
              >
                <Bookmark size={16} className="icon-mr" fill={isSaved ? 'currentColor' : 'none'} />
                {isSaved ? 'Saved' : 'Save Job'}
              </button>
            </div>

            {applyError && <span className="text-danger text-xs mt-1 block">{applyError}</span>}
            {saveError && <span className="text-warning text-xs mt-1 block">{saveError}</span>}
          </div>
        </div>
      </header>

      {/* Two-column layout: Left details & Right match intelligence */}
      <div className="job-details-split-layout">
        {/* Left Column: Job Description and Requirements */}
        <section className="job-content-col">
          {/* Structured Requirements from AI or ATS if present */}
          {reqs && (
            <div className="card structured-requirements-card">
              <h3 className="section-title-sm">
                <FileText size={18} className="icon-mr text-accent" />
                Structured Requirements
              </h3>

              {reqs.required_skills && reqs.required_skills.length > 0 && (
                <div className="req-group">
                  <h4 className="req-label">Required Skills</h4>
                  <div className="tags-flex">
                    {reqs.required_skills.map((s, idx) => (
                      <span key={idx} className="badge badge-accent">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {reqs.preferred_skills && reqs.preferred_skills.length > 0 && (
                <div className="req-group">
                  <h4 className="req-label">Preferred Skills</h4>
                  <div className="tags-flex">
                    {reqs.preferred_skills.map((s, idx) => (
                      <span key={idx} className="badge badge-secondary">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {reqs.minimum_years_experience !== undefined && (
                <div className="req-group">
                  <h4 className="req-label">Experience</h4>
                  <p className="text-sm">
                    {reqs.minimum_years_experience} years minimum relevant professional experience.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Job Description (Sanitized HTML) */}
          <div className="card job-description-card">
            <h3 className="section-title-sm">Job Description</h3>
            {sanitizedDescription ? (
              <div
                className="job-description-html"
                dangerouslySetInnerHTML={{ __html: sanitizedDescription }}
              />
            ) : (
              <p className="text-muted">No description provided for this opening.</p>
            )}
          </div>

          {/* Source Link */}
          {job.source_url && (
            <div className="job-source-footer">
              <span className="text-muted text-xs">
                Ingested from career portal URL:{' '}
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-accent"
                >
                  {job.source_url}
                </a>
              </span>
            </div>
          )}
        </section>

        {/* Right Column: Match Breakdown, Explanation & AI Insights */}
        <aside className="job-match-col">
          {/* AI Insights Card */}
          <AIInsightsCard
            aiExplanation={job.ai_explanation}
            deterministicFallback={{
              reasons: job.match_reasons,
              matchedCriteria: job.matched_criteria,
            }}
          />

          {/* Phase 13 Skill Gap & Ontology Card */}
          <SkillGapCard jobId={job.id} token={token} />

          {/* Deterministic Explanation Card */}
          <MatchExplanationCard
            reasons={job.match_reasons}
            matchedCriteria={job.matched_criteria}
            missingCriteria={job.missing_criteria}
          />

          {/* Match Score Breakdown */}
          <MatchBreakdownCard breakdown={job.breakdown} />
        </aside>
      </div>
    </div>
  )
}
