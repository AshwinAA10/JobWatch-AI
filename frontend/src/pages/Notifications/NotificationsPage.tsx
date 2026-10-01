import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  CheckCheck,
  Briefcase,
  Sparkles,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  fetchNotifications,
  markAllNotificationsAsRead,
  markNotificationAsRead,
} from '../../services/notifications'
import { NotificationItem } from '../../types/notifications'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { EmptyState } from '../../components/common/EmptyState'

export const NotificationsPage: React.FC = () => {
  const { token } = useAuth()
  const navigate = useNavigate()

  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false)
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [isMarkingAll, setIsMarkingAll] = useState<boolean>(false)

  const loadNotifications = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)

    try {
      const res = await fetchNotifications(token, {
        unreadOnly,
        limit: 50,
      })
      setNotifications(res.items)
      setTotal(res.total)
      setUnreadCount(res.unread_count)
    } catch (err: any) {
      setError(err.message || 'Failed to load notifications.')
    } finally {
      setIsLoading(false)
    }
  }, [token, unreadOnly])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  const handleMarkAsRead = async (notification: NotificationItem, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (!token || notification.is_read) return

    try {
      await markNotificationAsRead(token, notification.id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)),
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch {
      // ignore
    }
  }

  const handleNotificationClick = async (notification: NotificationItem) => {
    if (!notification.is_read) {
      await handleMarkAsRead(notification)
    }
    if (notification.job_id) {
      navigate(`/jobs/${notification.job_id}`)
    }
  }

  const handleMarkAllRead = async () => {
    if (!token || unreadCount === 0) return
    setIsMarkingAll(true)
    try {
      await markAllNotificationsAsRead(token)
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // ignore
    } finally {
      setIsMarkingAll(false)
    }
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'HIGH_QUALITY_MATCH':
        return <Sparkles size={18} className="text-accent" />
      case 'MONITORING_FAILURE':
        return <AlertTriangle size={18} className="text-warning" />
      default:
        return <Briefcase size={18} className="text-success" />
    }
  }

  return (
    <div className="notifications-page">
      <header className="page-header-actions">
        <div className="title-group">
          <div className="icon-badge">
            <Bell size={20} className="text-accent" />
          </div>
          <div>
            <h1 className="page-title">Alerts & Match Updates</h1>
            <p className="page-subtitle">
              Notifications triggered by new job postings meeting your threshold.
            </p>
          </div>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleMarkAllRead}
            disabled={isMarkingAll}
          >
            <CheckCheck size={15} className="icon-mr" />
            Mark All as Read
          </button>
        )}
      </header>

      {/* Filter Tabs */}
      <div className="notifications-tabs">
        <button
          type="button"
          className={`tab-btn ${!unreadOnly ? 'tab-btn-active' : ''}`}
          onClick={() => setUnreadOnly(false)}
        >
          All Notifications ({total})
        </button>
        <button
          type="button"
          className={`tab-btn ${unreadOnly ? 'tab-btn-active' : ''}`}
          onClick={() => setUnreadOnly(true)}
        >
          Unread Only {unreadCount > 0 && <span className="tab-pill">{unreadCount}</span>}
        </button>
      </div>

      {isLoading && <LoadingSkeleton count={4} type="line" />}

      {error && <ErrorMessage message={error} onRetry={loadNotifications} />}

      {!isLoading && !error && notifications.length === 0 && (
        <EmptyState
          title="You're all caught up"
          description={
            unreadOnly
              ? 'There are no unread notifications.'
              : 'You have not received any alerts yet. When new high-matching jobs appear, you will see them here.'
          }
          icon={<Bell size={42} strokeWidth={1.5} />}
        />
      )}

      {!isLoading && !error && notifications.length > 0 && (
        <div className="notifications-list" role="feed">
          {notifications.map((notif) => {
            const timeAgo = new Date(notif.created_at).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })

            return (
              <div
                key={notif.id}
                className={`notification-card ${!notif.is_read ? 'notification-card-unread' : ''}`}
                onClick={() => handleNotificationClick(notif)}
                role="article"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleNotificationClick(notif)
                }}
              >
                <div className="notif-icon-col">{getEventIcon(notif.event_type)}</div>

                <div className="notif-body-col">
                  <div className="notif-header-line">
                    <span className="notif-title">{notif.title}</span>
                    <span className="notif-time">{timeAgo}</span>
                  </div>

                  <p className="notif-desc">{notif.body}</p>

                  <div className="notif-footer-line">
                    {notif.payload?.match_score && (
                      <span className="badge badge-accent">
                        {Math.round(notif.payload.match_score)}% Match
                      </span>
                    )}
                    <span className="link-accent text-xs notif-view-job">
                      View Job Opening
                      <ArrowRight size={12} className="icon-ml" />
                    </span>
                  </div>
                </div>

                {!notif.is_read && (
                  <div className="notif-action-col">
                    <button
                      type="button"
                      className="btn-mark-read"
                      onClick={(e) => handleMarkAsRead(notif, e)}
                      title="Mark as read"
                      aria-label="Mark notification as read"
                    >
                      <div className="unread-dot" />
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
