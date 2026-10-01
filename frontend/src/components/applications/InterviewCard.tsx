import React, { useState } from 'react'
import {
  Calendar,
  Clock,
  User,
  MapPin,
  Video,
  CheckCircle,
  XCircle,
  Trash2,
  ExternalLink,
  Loader2,
} from 'lucide-react'
import { InterviewItem, InterviewStatus } from '../../types/application'

interface InterviewCardProps {
  interview: InterviewItem
  onStatusChange: (interviewId: string, status: InterviewStatus) => Promise<void>
  onDelete: (interviewId: string) => Promise<void>
}

export const InterviewCard: React.FC<InterviewCardProps> = ({
  interview,
  onStatusChange,
  onDelete,
}) => {
  const [isUpdating, setIsUpdating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const formatScheduledDate = (isoString: string) => {
    try {
      const date = new Date(isoString)
      return {
        dateStr: date.toLocaleDateString(undefined, {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }),
        timeStr: date.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
          timeZoneName: 'short',
        }),
      }
    } catch {
      return { dateStr: isoString, timeStr: '' }
    }
  }

  const { dateStr, timeStr } = formatScheduledDate(interview.scheduled_at)

  const handleUpdateStatus = async (newStatus: InterviewStatus) => {
    setIsUpdating(true)
    try {
      await onStatusChange(interview.id, newStatus)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to remove this scheduled interview round?')) return
    setIsDeleting(true)
    try {
      await onDelete(interview.id)
    } finally {
      setIsDeleting(false)
    }
  }

  const getStatusBadge = () => {
    switch (interview.status) {
      case 'COMPLETED':
        return <span className="badge badge-success flex-center gap-xs"><CheckCircle size={12} /> Completed</span>
      case 'CANCELLED':
        return <span className="badge badge-danger flex-center gap-xs"><XCircle size={12} /> Cancelled</span>
      case 'RESCHEDULED':
        return <span className="badge badge-warning flex-center gap-xs"><Clock size={12} /> Rescheduled</span>
      default:
        return <span className="badge badge-primary flex-center gap-xs"><Calendar size={12} /> Scheduled</span>
    }
  }

  return (
    <div className="interview-card card">
      <div className="card-header flex-between">
        <div className="interview-header-title">
          <span className="badge badge-secondary">{interview.interview_type}</span>
          <span className="interview-datetime font-medium ml-sm">
            {dateStr} · {timeStr}
          </span>
        </div>
        <div className="flex-center gap-sm">
          {getStatusBadge()}
          <button
            type="button"
            className="btn-icon text-muted hover-danger"
            onClick={handleDelete}
            disabled={isDeleting || isUpdating}
            aria-label="Delete interview"
            title="Delete interview"
          >
            {isDeleting ? <Loader2 size={14} className="spinner" /> : <Trash2 size={14} />}
          </button>
        </div>
      </div>

      <div className="card-body">
        <div className="interview-details-grid">
          {interview.duration_minutes && (
            <div className="detail-item flex-center gap-xs text-sm text-muted">
              <Clock size={14} />
              <span>{interview.duration_minutes} minutes</span>
            </div>
          )}

          {interview.interviewer_names && (
            <div className="detail-item flex-center gap-xs text-sm text-muted">
              <User size={14} />
              <span>{interview.interviewer_names}</span>
            </div>
          )}

          {interview.location && (
            <div className="detail-item flex-center gap-xs text-sm text-muted">
              <MapPin size={14} />
              <span>{interview.location}</span>
            </div>
          )}

          {interview.meeting_url && (
            <div className="detail-item flex-center gap-xs text-sm">
              <Video size={14} className="text-primary" />
              <a
                href={interview.meeting_url}
                target="_blank"
                rel="noopener noreferrer"
                className="link-primary flex-center gap-xs"
              >
                Join Meeting Link <ExternalLink size={12} />
              </a>
            </div>
          )}
        </div>

        {interview.notes && (
          <div className="interview-notes mt-sm">
            <p className="text-sm text-secondary bg-surface-alt p-sm rounded">
              {interview.notes}
            </p>
          </div>
        )}
      </div>

      {interview.status === 'SCHEDULED' && (
        <div className="card-footer flex-end gap-sm">
          <button
            type="button"
            className="btn btn-outline btn-xs"
            onClick={() => handleUpdateStatus('CANCELLED')}
            disabled={isUpdating}
          >
            Mark Cancelled
          </button>
          <button
            type="button"
            className="btn btn-primary btn-xs"
            onClick={() => handleUpdateStatus('COMPLETED')}
            disabled={isUpdating}
          >
            Mark Completed
          </button>
        </div>
      )}
    </div>
  )
}
