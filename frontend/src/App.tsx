import { useEffect, useState } from 'react'
import { fetchHealth } from './services/api'
import { HealthCheckResponse } from './types/api'

export function App() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    fetchHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data)
          setStatus('connected')
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setStatus('disconnected')
          setErrorMessage(err.message)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="container">
      <header className="header">
        <span className="badge">Phase 0</span>
        <h1 className="title">JobWatch AI</h1>
      </header>

      <p className="subtitle">
        Automated Career Portal Monitoring & Opportunity Intelligence.
        Phase 0 establishes the architectural boundaries and project foundation.
      </p>

      <div className="status-card">
        <div className="status-row">
          <span className="status-label">Phase</span>
          <span className="status-value">0 — Architecture & Project Setup</span>
        </div>
        <div className="status-row">
          <span className="status-label">Frontend Status</span>
          <span className="status-value status-healthy">Operational</span>
        </div>
        <div className="status-row">
          <span className="status-label">Backend Connection</span>
          <span
            className={`status-value ${
              status === 'connected'
                ? 'status-healthy'
                : status === 'checking'
                ? 'status-checking'
                : 'status-error'
            }`}
          >
            {status === 'connected' && `Healthy (${health?.version})`}
            {status === 'checking' && 'Connecting to /api/v1/health...'}
            {status === 'disconnected' && `Disconnected (${errorMessage || 'Offline'})`}
          </span>
        </div>
        {health && (
          <>
            <div className="status-row">
              <span className="status-label">Backend Environment</span>
              <span className="status-value">{health.environment}</span>
            </div>
            <div className="status-row">
              <span className="status-label">Last Health Ping</span>
              <span className="status-value">{new Date(health.timestamp).toLocaleTimeString()}</span>
            </div>
          </>
        )}
      </div>

      <p className="roadmap-preview">
        Next milestone: Phase 1 — Database + Backend Foundation (PostgreSQL, SQLAlchemy, Alembic)
      </p>
    </div>
  )
}

export default App
