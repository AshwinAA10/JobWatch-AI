import React, { useEffect, useState, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Building2,
  MapPin,
  Calendar,
  ExternalLink,
  Plus,
  Trash2,
  Video,
  Clock,
  AlertCircle,
  Loader2,
  Briefcase,
  History,
  HelpCircle,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchApplicationDetail,
  updateApplicationStatus,
  deleteApplication,
  createApplicationNote,
  deleteApplicationNote,
  createInterview,
  updateInterview,
  deleteInterview,
} from '../../services/applications'
import {
  ApplicationDetail,
  ApplicationStatus,
  InterviewCreatePayload,
  InterviewStatus,
} from '../../types/application'
import { ApplicationStatusBadge } from '../../components/applications/ApplicationStatusBadge'
import { ApplicationTimeline } from '../../components/applications/ApplicationTimeline'
import { ApplicationNotesCard } from '../../components/applications/ApplicationNotesCard'
import { InterviewCard } from '../../components/applications/InterviewCard'
import { InterviewModal } from '../../components/applications/InterviewModal'
import { MatchScoreBadge } from '../../components/matching/MatchScoreBadge'

const VALID_PROGRESSIONS: Record<string, ApplicationStatus[]> = {
  APPLIED: ['SCREENING', 'REJECTED', 'WITHDRAWN'],
  SCREENING: ['INTERVIEW', 'REJECTED', 'WITHDRAWN'],
  INTERVIEW: ['OFFER', 'REJECTED', 'WITHDRAWN'],
  OFFER: ['ACCEPTED', 'REJECTED', 'WITHDRAWN'],
  REJECTED: ['APPLIED', 'SCREENING', 'INTERVIEW'], // correction
  WITHDRAWN: ['APPLIED', 'SCREENING'], // correction
  ACCEPTED: ['WITHDRAWN'], // correction
}

export const ApplicationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { token, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [application, setApplication] = useState<ApplicationDetail | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Status transition state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false)
  const [statusNote, setStatusNote] = useState<string>('')
  const [showCorrectionMode, setShowCorrectionMode] = useState<boolean>(false)

  // Interview modal
  const [isInterviewModalOpen, setIsInterviewModalOpen] = useState<boolean>(false)

  // Deletion
  const [isDeletingApp, setIsDeletingApp] = useState<boolean>(false)

  const loadApplication = useCallback(async () => {
    if (!token || !id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchApplicationDetail(token, id)
      setApplication(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load application details.')
    } finally {
      setIsLoading(false)
    }
  }, [token, id])

  useEffect(() => {
    loadApplication()
  }, [loadApplication])

  const handleStatusChange = async (targetStatus: ApplicationStatus) => {
    if (!token || !id || !application) return

    // Confirmation for terminal states
    if (['REJECTED', 'WITHDRAWN', 'ACCEPTED'].includes(targetStatus)) {
      const confirmed = window.confirm(
        `Are you sure you want to change this application status to "${targetStatus}"?`,
      )
      if (!confirmed) return
    }

    setIsUpdatingStatus(true)
    try {
      const updated = await updateApplicationStatus(token, id, {
        status: targetStatus,
        note: statusNote.trim() || undefined,
      })
      setApplication(updated)
      setStatusNote('')
      setShowCorrectionMode(false)
    } catch (err: any) {
      alert(err.message || 'Failed to update application status.')
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  const handleDeleteApplication = async () => {
    if (!token || !id) return
    const confirmed = window.confirm(
      'Are you sure you want to permanently delete this tracked application and all its history, notes, and interviews?',
    )
    if (!confirmed) return

    setIsDeletingApp(true)
    try {
      await deleteApplication(token, id)
      navigate('/applications')
    } catch (err: any) {
      alert(err.message || 'Failed to delete application.')
      setIsDeletingApp(false)
    }
  }

  // Note actions
  const handleAddNote = async (content: string) => {
    if (!token || !id) return
    const newNote = await createApplicationNote(token, id, { content })
    setApplication((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        application_notes: [newNote, ...prev.application_notes],
      }
    })
  }

  const handleDeleteNote = async (noteId: string) => {
    if (!token || !id) return
    await deleteApplicationNote(token, id, noteId)
    setApplication((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        application_notes: prev.application_notes.filter((n) => n.id !== noteId),
      }
    })
  }

  // Interview actions
  const handleScheduleInterview = async (payload: InterviewCreatePayload) => {
    if (!token || !id) return
    const newInterview = await createInterview(token, id, payload)
    setApplication((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        interviews: [...prev.interviews, newInterview],
      }
    })
  }

  const handleInterviewStatusChange = async (interviewId: string, nextStatus: InterviewStatus) => {
    if (!token || !id) return
    const updated = await updateInterview(token, id, interviewId, { status: nextStatus })
    setApplication((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        interviews: prev.interviews.map((item) => (item.id === interviewId ? updated : item)),
      }
    })
  }

  const handleDeleteInterview = async (interviewId: string) => {
    if (!token || !id) return
    await deleteInterview(token, id, interviewId)
    setApplication((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        interviews: prev.interviews.filter((item) => item.id !== interviewId),
      }
    })
  }

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString(undefined, {
        month: 'long',
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
        <p className="text-muted">Please sign in to view this application.</p>
        <Link to="/login" className="btn btn-primary mt-md">Sign In</Link>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container py-xl text-center">
        <Loader2 size={36} className="spinner text-primary mx-auto mb-sm" />
        <p className="text-muted">Loading application details...</p>
      </div>
    )
  }

  if (error || !application) {
    return (
      <div className="container py-xl">
        <div className="alert alert-error mb-lg" role="alert">
          <AlertCircle size={18} />
          <span>{error || 'Application not found.'}</span>
        </div>
        <Link to="/applications" className="btn btn-outline flex-center gap-xs inline-flex">
          <ArrowLeft size={16} /> Back to Applications
        </Link>
      </div>
    )
  }

  const currentStatusNorm = (application.status || '').toUpperCase()
  const recommendedNext = VALID_PROGRESSIONS[currentStatusNorm] || ['APPLIED', 'REJECTED', 'WITHDRAWN']
  const allStatuses: ApplicationStatus[] = [
    'APPLIED',
    'SCREENING',
    'INTERVIEW',
    'OFFER',
    'ACCEPTED',
    'REJECTED',
    'WITHDRAWN',
  ]

  return (
    <div className="container application-detail-page py-lg" id="application-detail-container">
      {/* Back button & top actions */}
      <div className="page-top-nav flex-between mb-md">
        <Link to="/applications" className="btn btn-ghost btn-sm flex-center gap-xs text-muted">
          <ArrowLeft size={16} /> Back to Tracked Applications
        </Link>
        <button
          type="button"
          className="btn btn-ghost btn-sm text-danger hover-danger flex-center gap-xs"
          onClick={handleDeleteApplication}
          disabled={isDeletingApp}
        >
          {isDeletingApp ? <Loader2 size={14} className="spinner" /> : <Trash2 size={14} />}
          Delete Tracking
        </button>
      </div>

      {/* Main Header Card */}
      <section className="app-detail-header-card card mb-lg">
        <div className="flex-between flex-wrap gap-md">
          <div className="header-primary-info">
            <h1 className="heading-xl app-detail-title">{application.job_title}</h1>
            <div className="company-location-row flex-center gap-sm text-muted text-base mt-xs">
              <span className="flex-center gap-xs font-medium text-main">
                <Building2 size={16} />
                {application.company_name}
              </span>
              {application.job_location && (
                <>
                  <span className="meta-dot">·</span>
                  <span className="flex-center gap-xs">
                    <MapPin size={15} />
                    {application.job_location}
                  </span>
                </>
              )}
            </div>

            <div className="timestamps-row flex-center gap-lg text-xs text-muted mt-md">
              <span className="flex-center gap-xs">
                <Calendar size={13} />
                Applied on: <strong className="text-secondary">{formatDate(application.applied_at)}</strong>
              </span>
              <span className="flex-center gap-xs">
                <Clock size={13} />
                Status updated: <strong className="text-secondary">{formatDate(application.last_status_changed_at)}</strong>
              </span>
            </div>
          </div>

          <div className="header-badges-aside flex-col-end gap-sm">
            <div className="flex-center gap-sm">
              {application.match_score_at_application !== null && application.match_score_at_application !== undefined && (
                <MatchScoreBadge score={application.match_score_at_application} size="md" />
              )}
              <ApplicationStatusBadge status={application.status} size="lg" />
            </div>

            <div className="links-row flex-center gap-sm mt-sm">
              {application.external_application_url && (
                <a
                  href={application.external_application_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-outline btn-xs flex-center gap-xs"
                >
                  Career Portal <ExternalLink size={12} />
                </a>
              )}
              {application.job_id && (
                <Link to={`/jobs/${application.job_id}`} className="btn btn-secondary btn-xs flex-center gap-xs">
                  <Briefcase size={12} /> View Job Details
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Initial Submission Note */}
        {application.notes && (
          <div className="initial-submission-note mt-md p-sm bg-surface-alt rounded text-sm">
            <span className="text-xs text-muted block mb-xs font-semibold uppercase tracking-wider">
              Application Submission Note
            </span>
            <p className="text-secondary">{application.notes}</p>
          </div>
        )}
      </section>

      {/* Status Lifecycle Transition Action Bar */}
      <section className="status-lifecycle-card card mb-lg" aria-label="Update Application Status">
        <div className="card-header flex-between flex-wrap gap-xs">
          <div>
            <h2 className="card-title text-base flex-center gap-xs">
              <History size={16} className="text-primary" />
              Application Lifecycle Status
            </h2>
            <p className="text-xs text-muted mt-xs">
              Advance your application stage as you hear back from recruiters.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-xs text-muted"
            onClick={() => setShowCorrectionMode(!showCorrectionMode)}
          >
            {showCorrectionMode ? 'Hide Correction Mode' : 'Manual Correction Mode'}
          </button>
        </div>

        <div className="card-body">
          {/* Note for transition */}
          <div className="transition-note-field mb-md">
            <label htmlFor="transition-note-input" className="form-label text-xs text-muted">
              Add milestone note for this status change (optional)
            </label>
            <input
              id="transition-note-input"
              type="text"
              className="form-control form-control-sm"
              placeholder="e.g. Recruiter confirmed phone screen for next Thursday..."
              value={statusNote}
              onChange={(e) => setStatusNote(e.target.value)}
              disabled={isUpdatingStatus}
            />
          </div>

          {/* Quick Progression Buttons */}
          <div className="status-action-buttons flex-wrap gap-sm">
            <span className="text-xs text-muted flex-center font-medium mr-xs">Next Stage:</span>
            {recommendedNext.map((nextSt) => (
              <button
                key={nextSt}
                type="button"
                className={`btn btn-sm ${
                  nextSt === 'REJECTED' || nextSt === 'WITHDRAWN'
                    ? 'btn-outline text-muted hover-danger'
                    : 'btn-primary'
                }`}
                onClick={() => handleStatusChange(nextSt)}
                disabled={isUpdatingStatus}
              >
                {isUpdatingStatus ? (
                  <Loader2 size={14} className="spinner" />
                ) : (
                  `Move to ${nextSt}`
                )}
              </button>
            ))}
          </div>

          {/* Manual Correction Mode */}
          {showCorrectionMode && (
            <div className="manual-correction-box mt-md p-sm bg-surface-alt rounded">
              <p className="text-xs text-muted mb-sm flex-center gap-xs">
                <HelpCircle size={13} />
                Need to correct an accidental status update? You can manually select any state below.
              </p>
              <div className="flex-wrap gap-xs">
                {allStatuses.map((st) => (
                  <button
                    key={st}
                    type="button"
                    className={`btn btn-xs ${
                      application.status.toUpperCase() === st ? 'btn-secondary disabled' : 'btn-outline'
                    }`}
                    onClick={() => handleStatusChange(st)}
                    disabled={isUpdatingStatus || application.status.toUpperCase() === st}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Two column layout: Left (Interviews & Notes) | Right (Timeline Audit) */}
      <div className="app-detail-grid grid-2-1 gap-lg">
        {/* Left Column: Scheduled Interviews & Notes */}
        <div className="left-column space-y-lg">
          {/* Scheduled Interviews Section */}
          <section className="interviews-section card" aria-labelledby="interviews-title">
            <div className="card-header flex-between">
              <h2 id="interviews-title" className="card-title text-base flex-center gap-xs">
                <Video size={16} className="text-primary" />
                Interviews & Rounds ({application.interviews.length})
              </h2>
              <button
                type="button"
                className="btn btn-outline btn-xs flex-center gap-xs"
                onClick={() => setIsInterviewModalOpen(true)}
              >
                <Plus size={13} /> Schedule Round
              </button>
            </div>

            <div className="card-body">
              {application.interviews.length === 0 ? (
                <div className="text-center py-md">
                  <p className="text-muted text-sm mb-sm">
                    No interview rounds scheduled yet.
                  </p>
                  <button
                    type="button"
                    className="btn btn-primary btn-xs flex-center gap-xs mx-auto"
                    onClick={() => setIsInterviewModalOpen(true)}
                  >
                    <Plus size={13} /> Schedule First Round
                  </button>
                </div>
              ) : (
                <div className="interviews-stack space-y-md">
                  {application.interviews.map((interview) => (
                    <InterviewCard
                      key={interview.id}
                      interview={interview}
                      onStatusChange={handleInterviewStatusChange}
                      onDelete={handleDeleteInterview}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Notes Component */}
          <ApplicationNotesCard
            notes={application.application_notes}
            onAddNote={handleAddNote}
            onDeleteNote={handleDeleteNote}
          />
        </div>

        {/* Right Column: Status Timeline Audit Trail */}
        <div className="right-column">
          <section className="timeline-section card" aria-labelledby="timeline-title">
            <div className="card-header">
              <h2 id="timeline-title" className="card-title text-base flex-center gap-xs">
                <History size={16} className="text-primary" />
                Lifecycle Audit Timeline
              </h2>
              <span className="text-xs text-muted block mt-xs">
                Immutable record of all transitions
              </span>
            </div>
            <div className="card-body">
              <ApplicationTimeline history={application.history} />
            </div>
          </section>
        </div>
      </div>

      {/* Interview Modal */}
      <InterviewModal
        isOpen={isInterviewModalOpen}
        onClose={() => setIsInterviewModalOpen(false)}
        onSave={handleScheduleInterview}
      />
    </div>
  )
}
