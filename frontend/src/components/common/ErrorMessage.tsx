import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
}) => {
  return (
    <div className="error-message-box" role="alert">
      <div className="error-icon" aria-hidden="true">
        <AlertCircle size={28} />
      </div>
      <div className="error-content">
        <h4 className="error-title">{title}</h4>
        <p className="error-desc">{message}</p>
        {onRetry && (
          <button
            type="button"
            className="btn btn-secondary btn-sm error-retry-btn"
            onClick={onRetry}
          >
            <RefreshCw size={14} className="icon-mr" />
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}
