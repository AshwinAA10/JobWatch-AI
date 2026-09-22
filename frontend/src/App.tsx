import { useEffect, useState } from 'react'
import { fetchDbHealth, fetchHealth } from './services/api'
import { DatabaseHealthCheckResponse, HealthCheckResponse } from './types/api'

export function App() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [dbHealth, setDbHealth] = useState<DatabaseHealthCheckResponse | null>(null)
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
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

    fetchDbHealth()
      .then((data) => {
        if (isMounted) {
          setDbHealth(data)
          setDbStatus('connected')
        }
      })
      .catch(() => {
        if (isMounted) {
          setDbStatus('disconnected')
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="container">
      <header className="header">
        <span className="badge">Phase 4</span>
        <h1 className="title">JobWatch AI</h1>
      </header>

      <p className="subtitle">
        Automated Career Portal Monitoring & Opportunity Intelligence.
        Phase 4 establishes deterministic cross-source deduplication, job identity resolution, canonical linking, and false-positive prevention.
      </p>

      <div className="status-card">
        <div className="status-row">
          <span className="status-label">Phase</span>
          <span className="status-value">4 — Deduplication & Job Identity</span>
        </div>
        <div className="status-row">
          <span className="status-label">Frontend Status</span>
          <span className="status-value status-healthy">Operational</span>
        </div>
        <div className="status-row">
          <span className="status-label">Backend Process</span>
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
        <div className="status-row">
          <span className="status-label">Database Readiness</span>
          <span
            className={`status-value ${
              dbStatus === 'connected'
                ? 'status-healthy'
                : dbStatus === 'checking'
                ? 'status-checking'
                : 'status-error'
            }`}
          >
            {dbStatus === 'connected' && `Connected (${dbHealth?.latency_ms} ms)`}
            {dbStatus === 'checking' && 'Probing /api/v1/health/db...'}
            {dbStatus === 'disconnected' && 'Disconnected / Offline'}
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
        Next milestone: Phase 5 — User Profiles (Preferences, Resumes & Opportunity Criteria)
      </p>
    </div>
  )
}

export default App
