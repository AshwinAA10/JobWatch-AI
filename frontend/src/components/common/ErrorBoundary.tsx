import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('JobWatch AI Frontend Uncaught Error:', error, errorInfo)
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="error-boundary-view" role="alert">
          <div className="error-boundary-icon-box">
            <AlertTriangle size={32} />
          </div>
          <h2 className="error-boundary-title">
            Something went wrong
          </h2>
          <p className="error-boundary-desc">
            An unexpected error occurred while rendering this view. Your session data has been preserved.
          </p>
          <div className="error-boundary-actions">
            <button
              type="button"
              onClick={this.handleReset}
              className="btn btn-secondary btn-sm"
            >
              Try Again
            </button>
            <button
              type="button"
              onClick={this.handleReload}
              className="btn btn-primary btn-sm"
            >
              <RotateCcw size={15} className="icon-mr" />
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
