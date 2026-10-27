import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Sparkles,
  Briefcase,
  Bookmark,
  Bell,
  ArrowRight,
  TrendingUp,
  Radar,
  ChevronRight,
  Clock,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchJobs, fetchSavedJobs } from '../../services/jobs'
import { fetchNotifications } from '../../services/notifications'
import { fetchCandidateProfile } from '../../services/profile'
import { fetchApplicationStats } from '../../services/applications'
import { JobCard as JobCardType } from '../../types/job'
import { NotificationItem } from '../../types/notifications'
import { CandidateProfile } from '../../types/profile'
import { ApplicationStats } from '../../types/application'
import { JobCard } from '../../components/jobs/JobCard'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { EmptyState } from '../../components/common/EmptyState'

export const DashboardPage: React.FC = () => {
  const { user, token } = useAuth()
  const navigate = useNavigate()

  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [recommendedJobs, setRecommendedJobs] = useState<JobCardType[]>([])
  const [savedCount, setSavedCount] = useState<number>(0)
  const [recentAlerts, setRecentAlerts] = useState<NotificationItem[]>([])
  const [appStats, setAppStats] = useState<ApplicationStats | null>(null)
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
      const [jobsRes, savedRes, notifRes, profileRes, statsRes] = await Promise.all([
        fetchJobs({ sort_by: 'best_match', page_size: 6 }, token),
        fetchSavedJobs(token, 1, 1),
        fetchNotifications(token, { limit: 4 }),
        fetchCandidateProfile(token).catch(() => null),
        fetchApplicationStats(token).catch(() => null),
      ])

      setRecommendedJobs(jobsRes.items)
      setTotalJobs(jobsRes.total)
      setSavedCount(savedRes.total)
      setRecentAlerts(notifRes.items)
      setProfile(profileRes)
      if (statsRes) setAppStats(statsRes)

      // Count strong matches (score >= 80)
      const strong = jobsRes.items.filter((j) => (j.match_score || 0) >= 80).length
      setStrongMatchCount(strong)
    } catch (err: any) {
      setError(err.message || 'Unable to load dashboard intelligence data.')
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
      {/* Career Intelligence Radar Hero */}
      <section className="dashboard-hero" aria-label="Candidate intelligence status">
        <div className="hero-text-content">
          <div className="hero-telemetry-badge">
            <span className="radar-pulse-dot" aria-hidden="true" />
            <span className="telemetry-label font-mono">AUTONOMOUS RADAR ACTIVE</span>
          </div>
          <h1 className="hero-heading">
            {getGreeting()}, <span className="hero-name">{candidateName}</span>
          </h1>
          <p className="hero-subtext">
            Continuous career opportunity monitoring across connected company portals.
          </p>
        </div>

        {profile && (
          <div className="profile-completion-cta">
            <div className="completion-info">
              <span className="completion-label">Profile Match Calibration</span>
              <span className="completion-val font-mono">{profile.profile_completion_percent}%</span>
            </div>
            <div
              className="completion-bar-track"
              role="progressbar"
              aria-valuenow={profile.profile_completion_percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Profile match calibration percentage"
            >
              <div
                className="completion-bar-fill"
                style={{ width: `${profile.profile_completion_percent}%` }}
              />
            </div>
            <Link to="/profile" className="btn-link btn-xs mt-2 flex-center gap-2xs">
              <span>{profile.profile_completion_percent < 80 ? 'Calibrate skills to improve accuracy' : 'Edit candidate profile'}</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        )}
      </section>

      {/* Intelligence Command Strip */}
      <section className="dashboard-stats-grid" aria-label="Opportunity metrics">
        <Link to="/jobs?min_match=80" className="stat-card" title="View strong matches">
          <div className="stat-icon-wrapper stat-icon-sparkle">
            <Sparkles size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value font-mono">{isLoading ? '—' : strongMatchCount}</span>
            <span className="stat-label">Strong Matches (≥80%)</span>
          </div>
          <ChevronRight size={16} className="stat-card-arrow" />
        </Link>

        <Link to="/jobs" className="stat-card" title="Explore all open positions">
          <div className="stat-icon-wrapper stat-icon-briefcase">
            <Briefcase size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value font-mono">{isLoading ? '—' : totalJobs}</span>
            <span className="stat-label">Monitored Openings</span>
          </div>
          <ChevronRight size={16} className="stat-card-arrow" />
        </Link>

        <Link to="/saved" className="stat-card" title="View saved opportunities">
          <div className="stat-icon-wrapper stat-icon-bookmark">
            <Bookmark size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value font-mono">{isLoading ? '—' : savedCount}</span>
            <span className="stat-label">Saved Opportunities</span>
          </div>
          <ChevronRight size={16} className="stat-card-arrow" />
        </Link>

        <Link to="/notifications" className="stat-card" title="View recent alerts">
          <div className="stat-icon-wrapper stat-icon-bell">
            <Bell size={20} />
          </div>
          <div className="stat-info">
            <span className="stat-value font-mono">{isLoading ? '—' : recentAlerts.length}</span>
            <span className="stat-label">Recent Alerts</span>
          </div>
          <ChevronRight size={16} className="stat-card-arrow" />
        </Link>
      </section>

      {/* Application Progression Pipeline */}
      {appStats && (
        <section className="dashboard-applications-summary card mb-lg" aria-label="Application tracking overview">
          <div className="card-header flex-between flex-wrap gap-xs">
            <div>
              <h2 className="section-title text-base flex-center gap-xs">
                <Briefcase size={16} className="text-accent" />
                <span>Application Lifecycle Pipeline</span>
              </h2>
              <p className="section-desc text-xs">
                Real-time tracking of jobs you've applied to and upcoming progression
              </p>
            </div>
            <Link to="/applications" className="btn btn-secondary btn-xs flex-center gap-xs">
              <span>View All Applications ({appStats.total})</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="card-body">
            <div className="app-stats-row flex-between flex-wrap gap-sm">
              <Link to="/applications" className="app-stat-pill">
                <span className="pill-count font-mono">{appStats.total}</span>
                <span className="pill-title">All</span>
              </Link>
              <Link to="/applications?status=APPLIED" className="app-stat-pill pill-applied">
                <span className="pill-count font-mono">{appStats.applied}</span>
                <span className="pill-title">Applied</span>
              </Link>
              <Link to="/applications?status=SCREENING" className="app-stat-pill pill-screening">
                <span className="pill-count font-mono">{appStats.screening}</span>
                <span className="pill-title">Screening</span>
              </Link>
              <Link to="/applications?status=INTERVIEW" className="app-stat-pill pill-interview">
                <span className="pill-count font-mono">{appStats.interview}</span>
                <span className="pill-title">Interview</span>
              </Link>
              <Link to="/applications?status=OFFER" className="app-stat-pill pill-offer">
                <span className="pill-count font-mono">{appStats.offer}</span>
                <span className="pill-title">Offer</span>
              </Link>
              <Link to="/applications?status=REJECTED" className="app-stat-pill pill-rejected">
                <span className="pill-count font-mono">{appStats.rejected}</span>
                <span className="pill-title">Rejected</span>
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Main Grid: Recommended Opportunities & Intelligence Stream */}
      <div className="dashboard-split-layout">
        {/* Recommended Jobs */}
        <section className="dashboard-main-col" aria-label="Recommended job discoveries">
          <div className="section-header-flex">
            <div>
              <div className="flex-center gap-xs mb-1">
                <h2 className="section-title">Top Career Matches</h2>
                <span className="badge badge-accent font-mono text-xs">AI Ranked</span>
              </div>
              <p className="section-desc">Highest scoring opportunities matching your verified skills and target preferences</p>
            </div>
            <Link to="/jobs" className="btn btn-secondary btn-sm flex-center gap-xs">
              <span>Explore All Jobs</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          {isLoading && <LoadingSkeleton count={3} type="card" />}

          {error && <ErrorMessage message={error} onRetry={loadDashboardData} />}

          {!isLoading && !error && recommendedJobs.length === 0 && (
            <EmptyState
              title="No matching opportunities discovered yet"
              description="Our autonomous engine is monitoring connected company portals. As new openings match your criteria, they will appear here."
              actionLabel="Explore All Openings"
              onAction={() => navigate('/jobs')}
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

        {/* Aside: Alerts & Intelligence Radar */}
        <aside className="dashboard-aside-col" aria-label="Alerts and portal telemetry">
          {/* Recent Alerts Card */}
          <div className="card dashboard-alerts-widget">
            <div className="widget-header">
              <div className="widget-title-group flex-center gap-xs">
                <Bell size={16} className="text-accent" />
                <h3 className="widget-title">Recent Radar Alerts</h3>
              </div>
              <Link to="/notifications" className="btn-link btn-xs">
                View all
              </Link>
            </div>

            {recentAlerts.length === 0 ? (
              <p className="text-muted text-sm py-2">
                All caught up. No recent notifications.
              </p>
            ) : (
              <ul className="widget-alerts-list">
                {recentAlerts.map((alert) => (
                  <li key={alert.id} className="widget-alert-item">
                    <Link to={`/jobs/${alert.job_id}`} className="alert-item-link">
                      <span className="alert-title">{alert.title}</span>
                      <p className="alert-snippet">{alert.body}</p>
                      <span className="alert-time font-mono text-xs text-muted flex-center gap-2xs mt-1">
                        <Clock size={11} />
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

          {/* Autonomous Monitoring Status Card */}
          <div className="card dashboard-tip-card">
            <div className="tip-header flex-center gap-xs mb-2">
              <Radar size={16} className="text-accent" />
              <h4 className="tip-title">Autonomous Monitoring</h4>
            </div>
            <p className="tip-text text-sm text-secondary">
              Direct telemetry connects to Greenhouse, Lever, and Workday portals. Deduplication groups identical multi-postings into canonical listings.
            </p>
            <div className="portal-badges-row flex-wrap gap-xs mt-2">
              <span className="badge badge-secondary text-xs">Greenhouse</span>
              <span className="badge badge-secondary text-xs">Lever</span>
              <span className="badge badge-secondary text-xs">Workday</span>
            </div>
            <Link to="/settings" className="btn btn-secondary btn-xs mt-3 flex-center gap-xs">
              <span>Configure Thresholds & Webhooks</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          {/* Profile Calibration Shortcut */}
          <div className="card dashboard-tip-card">
            <div className="tip-header flex-center gap-xs mb-2">
              <TrendingUp size={16} className="text-accent" />
              <h4 className="tip-title">Match Accuracy Calibration</h4>
            </div>
            <p className="tip-text text-sm text-secondary">
              Semantic fit improves when all technical skills and seniority years are populated in your profile.
            </p>
            <Link to="/profile" className="btn btn-secondary btn-xs mt-3 flex-center gap-xs">
              <span>Update Skills & Experience</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
