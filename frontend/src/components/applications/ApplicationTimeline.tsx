import React from 'react'
import { Check, Clock } from 'lucide-react'
import { ApplicationHistoryItem } from '../../types/application'
import { ApplicationStatusBadge } from './ApplicationStatusBadge'

interface ApplicationTimelineProps {
  history: ApplicationHistoryItem[]
  className?: string
}

export const ApplicationTimeline: React.FC<ApplicationTimelineProps> = ({
  history,
  className = '',
}) => {
  if (!history || history.length === 0) {
    return (
      <div className={`timeline-empty ${className}`}>
        <p className="text-muted">No timeline events recorded yet.</p>
      </div>
    )
  }

  // Sort ascending for chronological top-to-bottom story
  const sorted = [...history].sort(
    (a, b) => new Date(a.changed_at).getTime() - new Date(b.changed_at).getTime(),
  )

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString)
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className={`application-timeline ${className}`} role="feed" aria-label="Application Status Timeline">
      <ol className="timeline-list">
        {sorted.map((item, index) => {
          const isLatest = index === sorted.length - 1
          return (
            <li
              key={item.id}
              className={`timeline-item ${isLatest ? 'timeline-item-latest' : ''}`}
              aria-current={isLatest ? 'step' : undefined}
            >
              <div className="timeline-node">
                <div className="timeline-dot">
                  {isLatest ? <Check size={14} /> : <span className="dot-inner" />}
                </div>
                {!isLatest && <div className="timeline-line" aria-hidden="true" />}
              </div>

              <div className="timeline-content">
                <div className="timeline-header">
                  <div className="timeline-status-wrapper">
                    <ApplicationStatusBadge status={item.new_status} size="sm" />
                    {item.old_status && (
                      <span className="timeline-transition-sub text-muted">
                        from {item.old_status.toLowerCase()}
                      </span>
                    )}
                  </div>
                  <time className="timeline-timestamp" dateTime={item.changed_at}>
                    <Clock size={12} className="inline-icon" />
                    {formatDate(item.changed_at)}
                  </time>
                </div>

                {item.note && (
                  <div className="timeline-note">
                    <p className="timeline-note-text">"{item.note}"</p>
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
