import React, { useState } from 'react'
import { X, Calendar, Loader2, AlertCircle } from 'lucide-react'
import { InterviewCreatePayload, InterviewType } from '../../types/application'

interface InterviewModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (payload: InterviewCreatePayload) => Promise<void>
}

export const InterviewModal: React.FC<InterviewModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [interviewType, setInterviewType] = useState<InterviewType>('TECHNICAL')
  const [scheduledAt, setScheduledAt] = useState('')
  const [durationMinutes, setDurationMinutes] = useState('60')
  const [interviewerNames, setInterviewerNames] = useState('')
  const [location, setLocation] = useState('')
  const [meetingUrl, setMeetingUrl] = useState('')
  const [notes, setNotes] = useState('')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scheduledAt) {
      setError('Please select a scheduled date and time.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const utcDate = new Date(scheduledAt).toISOString()
      await onSave({
        interview_type: interviewType,
        scheduled_at: utcDate,
        duration_minutes: durationMinutes ? parseInt(durationMinutes, 10) : undefined,
        interviewer_names: interviewerNames.trim() || undefined,
        location: location.trim() || undefined,
        meeting_url: meetingUrl.trim() || undefined,
        notes: notes.trim() || undefined,
      })
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to schedule interview round.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="interview-modal-title">
      <div className="modal-content modal-md">
        <div className="modal-header flex-between">
          <h3 id="interview-modal-title" className="modal-title flex-center gap-xs">
            <Calendar size={18} className="text-primary" />
            Schedule Interview Round
          </h3>
          <button
            type="button"
            className="btn-icon"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body space-y-md">
            {error && (
              <div className="alert alert-error" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="interview-type-select" className="form-label">
                Interview Type *
              </label>
              <select
                id="interview-type-select"
                className="form-control"
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value as InterviewType)}
                disabled={isSubmitting}
              >
                <option value="PHONE">Phone Screen</option>
                <option value="TECHNICAL">Technical Interview</option>
                <option value="HR">HR / Culture Fit</option>
                <option value="BEHAVIORAL">Behavioral</option>
                <option value="MANAGERIAL">Hiring Manager</option>
                <option value="FINAL">Final Round</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div className="form-grid grid-2">
              <div className="form-group">
                <label htmlFor="scheduled-datetime-input" className="form-label">
                  Date & Time * (Local Time)
                </label>
                <input
                  id="scheduled-datetime-input"
                  type="datetime-local"
                  className="form-control"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="duration-input" className="form-label">
                  Duration (Minutes)
                </label>
                <input
                  id="duration-input"
                  type="number"
                  min="1"
                  max="480"
                  className="form-control"
                  placeholder="60"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="interviewers-input" className="form-label">
                Interviewer(s)
              </label>
              <input
                id="interviewers-input"
                type="text"
                className="form-control"
                placeholder="e.g. Sarah Jenkins (Engineering Manager)"
                value={interviewerNames}
                onChange={(e) => setInterviewerNames(e.target.value)}
                disabled={isSubmitting}
                maxLength={255}
              />
            </div>

            <div className="form-grid grid-2">
              <div className="form-group">
                <label htmlFor="location-input" className="form-label">
                  Location / Platform
                </label>
                <input
                  id="location-input"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Google Meet, Zoom, Office HQ"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={isSubmitting}
                  maxLength={255}
                />
              </div>

              <div className="form-group">
                <label htmlFor="meeting-url-input" className="form-label">
                  Meeting URL
                </label>
                <input
                  id="meeting-url-input"
                  type="url"
                  className="form-control"
                  placeholder="https://..."
                  value={meetingUrl}
                  onChange={(e) => setMeetingUrl(e.target.value)}
                  disabled={isSubmitting}
                  maxLength={2048}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="interview-notes-input" className="form-label">
                Preparation / Notes
              </label>
              <textarea
                id="interview-notes-input"
                rows={2}
                className="form-control"
                placeholder="Key talking points, technical areas to review, interviewer bio..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={isSubmitting}
                maxLength={5000}
              />
            </div>
          </div>

          <div className="modal-footer flex-end gap-sm">
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex-center gap-xs"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={16} className="spinner" />
                  Scheduling...
                </>
              ) : (
                'Schedule Interview'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
