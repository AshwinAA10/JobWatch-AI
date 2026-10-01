import React, { useEffect, useState, useCallback } from 'react'
import {
  Settings,
  Bell,
  Briefcase,
  Save,
  Check,
  Mail,
  Webhook,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchCandidatePreferences,
  updateCandidatePreferences,
} from '../../services/profile'
import {
  fetchNotificationPreferences,
  updateNotificationPreferences,
} from '../../services/notifications'
import {
  CandidatePreferencesUpdate,
} from '../../types/profile'
import {
  NotificationPreferenceUpdate,
} from '../../types/notifications'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'

export const SettingsPage: React.FC = () => {
  const { token } = useAuth()

  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Job Preferences Form State
  const [desiredTitles, setDesiredTitles] = useState<string>('')
  const [preferredLocations, setPreferredLocations] = useState<string>('')
  const [workplaceRemote, setWorkplaceRemote] = useState<boolean>(true)
  const [workplaceHybrid, setWorkplaceHybrid] = useState<boolean>(true)
  const [workplaceOnsite, setWorkplaceOnsite] = useState<boolean>(false)
  const [minSalary, setMinSalary] = useState<string>('')
  const [maxSalary, setMaxSalary] = useState<string>('')
  const [willingToRelocate, setWillingToRelocate] = useState<boolean>(false)

  // Notification Preferences Form State
  const [emailEnabled, setEmailEnabled] = useState<boolean>(true)
  const [webhookEnabled, setWebhookEnabled] = useState<boolean>(false)
  const [webhookUrl, setWebhookUrl] = useState<string>('')
  const [minScoreThreshold, setMinScoreThreshold] = useState<number>(70)
  const [frequency, setFrequency] = useState<'IMMEDIATE' | 'DAILY_DIGEST'>('IMMEDIATE')
  const [maxPerHour, setMaxPerHour] = useState<number>(10)

  const [isSavingJobs, setIsSavingJobs] = useState<boolean>(false)
  const [isSavingNotifs, setIsSavingNotifs] = useState<boolean>(false)

  const loadPreferences = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)

    try {
      const [jp, np] = await Promise.all([
        fetchCandidatePreferences(token).catch(() => null),
        fetchNotificationPreferences(token).catch(() => null),
      ])

      if (jp) {
        setDesiredTitles(jp.desired_titles?.join(', ') || '')
        setPreferredLocations(jp.preferred_locations?.join(', ') || '')
        setWorkplaceRemote(jp.workplace_types?.includes('REMOTE') ?? true)
        setWorkplaceHybrid(jp.workplace_types?.includes('HYBRID') ?? true)
        setWorkplaceOnsite(jp.workplace_types?.includes('ONSITE') ?? false)
        setMinSalary(jp.minimum_salary ? jp.minimum_salary.toString() : '')
        setMaxSalary(jp.maximum_salary ? jp.maximum_salary.toString() : '')
        setWillingToRelocate(jp.willing_to_relocate ?? false)
      }

      if (np) {
        setEmailEnabled(np.email_enabled)
        setWebhookEnabled(np.webhook_enabled)
        setWebhookUrl(np.webhook_url || '')
        setMinScoreThreshold(Math.round(np.minimum_match_score))
        setFrequency(np.frequency)
        setMaxPerHour(np.max_per_hour)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load user preferences.')
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  const flashSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 4000)
  }

  // Save Job Preferences
  const handleSaveJobPrefs = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return

    setIsSavingJobs(true)
    setError(null)

    const workplaceTypes: any[] = []
    if (workplaceRemote) workplaceTypes.push('REMOTE')
    if (workplaceHybrid) workplaceTypes.push('HYBRID')
    if (workplaceOnsite) workplaceTypes.push('ONSITE')

    const titles = desiredTitles
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)

    const locs = preferredLocations
      .split(',')
      .map((l) => l.trim())
      .filter(Boolean)

    const payload: CandidatePreferencesUpdate = {
      desired_titles: titles,
      preferred_locations: locs,
      workplace_types: workplaceTypes,
      minimum_salary: minSalary ? parseInt(minSalary, 10) : undefined,
      maximum_salary: maxSalary ? parseInt(maxSalary, 10) : undefined,
      willing_to_relocate: willingToRelocate,
    }

    try {
      await updateCandidatePreferences(token, payload)
      flashSuccess('Job preferences saved successfully.')
    } catch (err: any) {
      setError(err.message || 'Failed to save job preferences.')
    } finally {
      setIsSavingJobs(false)
    }
  }

  // Save Notification Preferences
  const handleSaveNotificationPrefs = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return

    setIsSavingNotifs(true)
    setError(null)

    const payload: NotificationPreferenceUpdate = {
      email_enabled: emailEnabled,
      webhook_enabled: webhookEnabled,
      webhook_url: webhookEnabled ? webhookUrl.trim() || null : null,
      minimum_match_score: minScoreThreshold,
      frequency,
      max_per_hour: maxPerHour,
    }

    try {
      await updateNotificationPreferences(token, payload)
      flashSuccess('Alert preferences saved successfully.')
    } catch (err: any) {
      setError(err.message || 'Failed to save notification preferences.')
    } finally {
      setIsSavingNotifs(false)
    }
  }

  if (isLoading) {
    return (
      <div className="settings-page-loading">
        <LoadingSkeleton count={2} type="card" />
      </div>
    )
  }

  return (
    <div className="settings-page">
      <header className="page-header-simple">
        <div className="title-group">
          <div className="icon-badge">
            <Settings size={20} className="text-accent" />
          </div>
          <div>
            <h1 className="page-title">Candidate Preferences & Settings</h1>
            <p className="page-subtitle">
              Fine-tune opportunity matching criteria and autonomous alert thresholds.
            </p>
          </div>
        </div>
      </header>

      {successMessage && (
        <div className="toast-success" role="status">
          <Check size={16} className="icon-mr" />
          {successMessage}
        </div>
      )}

      {error && <ErrorMessage message={error} onRetry={loadPreferences} />}

      <div className="settings-grid">
        {/* Section 1: Job Preferences */}
        <div className="card settings-card">
          <div className="card-header-clean">
            <div>
              <h3 className="section-title-sm">
                <Briefcase size={18} className="icon-mr text-accent" />
                Job Matching Preferences
              </h3>
              <p className="text-muted text-xs">
                Informs the matching engine on roles, locations, and workplace models.
              </p>
            </div>
          </div>

          <form onSubmit={handleSaveJobPrefs} className="settings-form">
            <div className="form-group">
              <label htmlFor="pref-titles" className="form-label">
                Desired Job Titles (comma-separated)
              </label>
              <input
                id="pref-titles"
                type="text"
                className="form-input"
                placeholder="e.g. Senior Software Engineer, Full Stack Developer, Tech Lead"
                value={desiredTitles}
                onChange={(e) => setDesiredTitles(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="pref-locations" className="form-label">
                Preferred Locations (comma-separated)
              </label>
              <input
                id="pref-locations"
                type="text"
                className="form-input"
                placeholder="e.g. San Francisco, CA, New York, NY, Austin, TX"
                value={preferredLocations}
                onChange={(e) => setPreferredLocations(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Workplace Arrangements</label>
              <div className="checkbox-row-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={workplaceRemote}
                    onChange={(e) => setWorkplaceRemote(e.target.checked)}
                  />
                  <span>Remote</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={workplaceHybrid}
                    onChange={(e) => setWorkplaceHybrid(e.target.checked)}
                  />
                  <span>Hybrid</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={workplaceOnsite}
                    onChange={(e) => setWorkplaceOnsite(e.target.checked)}
                  />
                  <span>On-Site</span>
                </label>
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label htmlFor="min-sal" className="form-label">
                  Minimum Target Salary (USD)
                </label>
                <input
                  id="min-sal"
                  type="number"
                  step="5000"
                  className="form-input"
                  placeholder="e.g. 140000"
                  value={minSalary}
                  onChange={(e) => setMinSalary(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="max-sal" className="form-label">
                  Maximum Target Salary (USD)
                </label>
                <input
                  id="max-sal"
                  type="number"
                  step="5000"
                  className="form-input"
                  placeholder="e.g. 200000"
                  value={maxSalary}
                  onChange={(e) => setMaxSalary(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={willingToRelocate}
                  onChange={(e) => setWillingToRelocate(e.target.checked)}
                />
                <span>Willing to relocate for the right role</span>
              </label>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm" disabled={isSavingJobs}>
                <Save size={14} className="icon-mr" />
                {isSavingJobs ? 'Saving...' : 'Save Job Preferences'}
              </button>
            </div>
          </form>
        </div>

        {/* Section 2: Alert & Notification Preferences */}
        <div className="card settings-card">
          <div className="card-header-clean">
            <div>
              <h3 className="section-title-sm">
                <Bell size={18} className="icon-mr text-accent" />
                Notification & Alert Channels
              </h3>
              <p className="text-muted text-xs">
                Configure when and where JobWatch AI delivers high-match opportunity alerts.
              </p>
            </div>
          </div>

          <form onSubmit={handleSaveNotificationPrefs} className="settings-form">
            {/* Score threshold slider */}
            <div className="form-group">
              <div className="slider-label-row">
                <label htmlFor="score-threshold-slider" className="form-label">
                  Minimum Match Score Threshold
                </label>
                <span className="badge badge-accent">{minScoreThreshold}% Fit</span>
              </div>
              <input
                id="score-threshold-slider"
                type="range"
                min="50"
                max="95"
                step="5"
                className="form-range"
                value={minScoreThreshold}
                onChange={(e) => setMinScoreThreshold(parseInt(e.target.value, 10))}
              />
              <span className="form-hint">
                Only notify me when an ingested opportunity scores {minScoreThreshold}% or higher.
              </span>
            </div>

            {/* Email Notifications */}
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={emailEnabled}
                  onChange={(e) => setEmailEnabled(e.target.checked)}
                />
                <span>
                  <Mail size={14} className="icon-mr inline-icon" />
                  Enable Email Notifications
                </span>
              </label>
            </div>

            {/* Webhook Notifications */}
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={webhookEnabled}
                  onChange={(e) => setWebhookEnabled(e.target.checked)}
                />
                <span>
                  <Webhook size={14} className="icon-mr inline-icon" />
                  Enable Custom Webhook Delivery
                </span>
              </label>

              {webhookEnabled && (
                <div className="webhook-url-box mt-2">
                  <label htmlFor="webhook-input" className="form-label">
                    Webhook Endpoint URL (POST JSON)
                  </label>
                  <input
                    id="webhook-input"
                    type="url"
                    className="form-input"
                    placeholder="https://your-domain.com/webhooks/jobs"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    required={webhookEnabled}
                  />
                </div>
              )}
            </div>

            {/* Notification Frequency */}
            <div className="form-group">
              <label htmlFor="notif-frequency" className="form-label">
                Notification Frequency
              </label>
              <select
                id="notif-frequency"
                className="form-select"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as any)}
              >
                <option value="IMMEDIATE">Immediate (as opportunities are detected)</option>
                <option value="DAILY_DIGEST">Daily Digest</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="max-alerts" className="form-label">
                Max Alert Rate (Alerts Per Hour)
              </label>
              <input
                id="max-alerts"
                type="number"
                min="1"
                max="50"
                className="form-input"
                value={maxPerHour}
                onChange={(e) => setMaxPerHour(parseInt(e.target.value, 10) || 5)}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm" disabled={isSavingNotifs}>
                <Save size={14} className="icon-mr" />
                {isSavingNotifs ? 'Saving...' : 'Save Alert Settings'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
