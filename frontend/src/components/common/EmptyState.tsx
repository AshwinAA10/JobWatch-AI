import React from 'react'
import { FolderSearch } from 'lucide-react'

interface EmptyStateProps {
  title?: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  icon?: React.ReactNode
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = "We couldn't find anything matching your criteria.",
  actionLabel,
  onAction,
  icon,
}) => {
  return (
    <div className="empty-state-container" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">
        {icon || <FolderSearch size={44} strokeWidth={1.5} />}
      </div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-desc">{description}</p>
      {actionLabel && onAction && (
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onAction}
          aria-label={actionLabel}
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
