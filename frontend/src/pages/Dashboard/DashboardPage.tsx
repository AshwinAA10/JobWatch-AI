import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Sparkles,
  Briefcase,
  Bookmark,
  Bell,
  ArrowRight,
  TrendingUp,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchJobs, fetchSavedJobs } from '../../services/jobs'
import { fetchNotifications } from '../../services/notifications'
import { fetchCandidateProfile } from '../../services/profile'
import { JobCard as JobCardType } from '../../types/job'
import { NotificationItem } from '../../types/notifications'
import { CandidateProfile } from '../../types/profile'
import { JobCard } from '../../components/jobs/JobCard'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { EmptyState } from '../../components/common/EmptyState'

export const DashboardPage: React.FC = () => {
  const { user, token } = useAuth()

  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [recommendedJobs, setRecommendedJobs] = useState<JobCardType[]>([])
  const [savedCount, setSavedCount] = useState<number>(0)
  const [recentAlerts, setRecentAlerts] = useState<NotificationItem[]>([])
  const [totalJobs, setTotalJobs] = useState<number>(0)
  const [strongMatchCount, setStrongMatchCount] = useState<number>(0)

  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadDashboardData = async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)

    try {
      // Parallel loading to avoid waterfall
      const [jobsRes, savedRes, notifRes, profileRes] = await Promise.all([
        fetchJobs({ sort_by: 'best_match', page_size: 6 }, token),
        fetchSavedJobs(token, 1, 1),
        fetchNotifications(token, { limit: 4 }),
        fetchCandidateProfile(token).catch(() => null),
      ])

      setRecommendedJobs(jobsRes.items)
      setTotalJobs(jobsRes.total)
      setSavedCount(savedRes.total)
      setRecentAlerts(notifRes.items)
      setProfile(profileRes)

      // Count strong matches (score >= 80)
      const strong = jobsRes.items.filter((j) => (j.match_score || 0) >= 80).length
      setStrongMatchCount(strong)
    } catch (err: any) {
      setError(err.message || 'Unable to load dashboard data.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [token])

  // Get greeting
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const candidateName = profile?.first_name || user?.email?.split('@')[0] || 'Candidate'

  return (
    <div className="dashboard-page">
      {/* Welcome Banner */}
      <section className="dashboard-hero">
        <div className="hero-text-content">
          <span className="hero-pill">Candidate Intelligence</span>
          <h1 className="hero-heading">
            {getGreeting()}, <span className="hero-name">{candidateName}</span>
          </h1>
          <p className="hero-subtext">
            Here are your top-scoring career opportunities and recent match updates.
          </p>
        </div>

        {profile && profile.profile_completion_percent < 80 && (
          <div className="profile-completion-cta">
            <div className="completion-info">
              <span className="completion-label">Profile Strength</span>
              <span className="completion-val">{profile.profile_completion_percent}%</span>
            </div>
            <div className="completion-bar-track">
              <div
                className="completion-bar-fill"
                style={{ width: `${profile.profile_completion_percent}%` }}
              />
            </div>
            <Link to="/profile" className="btn-link btn-xs mt-1">
              Add skills to improve matching accuracy →
            </Link>
          </div>
        )}
      </section>

      {/* Metrics Row */}
      <section className="dashboard-stats-grid" aria-label="Quick metrics">
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-sparkle">
            <Sparkles size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{isLoading ? '—' : strongMatchCount}</span>
            <span className="stat-label">Strong Matches</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-briefcase">
            <Briefcase size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{isLoading ? '—' : totalJobs}</span>
            <span className="stat-label">Open Positions</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-bookmark">
            <Bookmark size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{isLoading ? '—' : savedCount}</span>
            <span className="stat-label">Saved Jobs</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-bell">
            <Bell size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{isLoading ? '—' : recentAlerts.length}</span>
            <span className="stat-label">Recent Alerts</span>
          </div>
        </div>
      </section>

      {/* Main Grid: Recommended Jobs & Recent Alerts */}
      <div className="dashboard-split-layout">
        {/* Recommended Jobs */}
        <section className="dashboard-main-col">
          <div className="section-header-flex">
            <div>
              <h2 className="section-title">Recommended For You</h2>
              <p className="section-desc">Highest scoring opportunities matching your profile</p>
            </div>
            <Link to="/jobs" className="btn btn-secondary btn-sm">
              Explore All Jobs
              <ArrowRight size={14} className="icon-ml" />
            </Link>
          </div>

          {isLoading && <LoadingSkeleton count={3} type="card" />}

          {error && <ErrorMessage message={error} onRetry={loadDashboardData} />}

          {!isLoading && !error && recommendedJobs.length === 0 && (
            <EmptyState
              title="No matching jobs yet"
              description="We are actively monitoring career portals for openings that match your skills."
              actionLabel="Browse All Openings"
              onAction={() => (window.location.href = '/jobs')}
            />
          )}

          {!isLoading && !error && recommendedJobs.length > 0 && (
            <div className="job-cards-list">
              {recommendedJobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </section>

        {/* Aside: Alerts & Quick Links */}
        <aside className="dashboard-aside-col">
          <div className="card dashboard-alerts-widget">
            <div className="widget-header">
              <div className="widget-title-group">
                <Bell size={18} className="icon-mr text-accent" />
                <h3 className="widget-title">Recent Alerts</h3>
              </div>
              <Link to="/notifications" className="btn-link btn-xs">
                View all
              </Link>
            </div>

            {recentAlerts.length === 0 ? (
              <p className="text-muted text-sm" style={{ padding: '1rem 0' }}>
                You're all caught up! No recent notifications.
              </p>
            ) : (
              <ul className="widget-alerts-list">
                {recentAlerts.map((alert) => (
                  <li key={alert.id} className="widget-alert-item">
                    <Link to={`/jobs/${alert.job_id}`} className="alert-item-link">
                      <span className="alert-title">{alert.title}</span>
                      <p className="alert-snippet">{alert.body}</p>
                      <span className="alert-time">
                        {new Date(alert.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Tips / Intelligence Info */}
          <div className="card dashboard-tip-card">
            <div className="tip-header">
              <TrendingUp size={16} className="text-accent icon-mr" />
              <h4 className="tip-title">Autonomous Monitoring</h4>
            </div>
            <p className="tip-text">
              JobWatch AI periodically scans Greenhouse, Lever, and Workday sources for fresh openings.
              Keep your profile skills and desired titles updated to maximize match accuracy.
            </p>
            <Link to="/settings" className="btn btn-secondary btn-xs mt-2">
              Configure Alert Preferences
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
