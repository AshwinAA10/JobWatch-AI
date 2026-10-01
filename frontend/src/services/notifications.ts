/**
 * API client service for candidate notification preferences and alerts.
 */

import {
  NotificationItem,
  NotificationListResponse,
  NotificationPreference,
  NotificationPreferenceUpdate,
} from '../types/notifications'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export async function fetchNotificationPreferences(token: string): Promise<NotificationPreference> {
  const response = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch notification preferences: ${response.status}`)
  }
  return response.json()
}

export async function updateNotificationPreferences(
  token: string,
  update: NotificationPreferenceUpdate,
): Promise<NotificationPreference> {
  const response = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(update),
  })
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to update notification preferences: ${response.status}`)
  }
  return response.json()
}

export async function fetchNotifications(
  token: string,
  options: {
    status?: string
    eventType?: string
    unreadOnly?: boolean
    skip?: number
    limit?: number
  } = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams()
  if (options.status) params.append('status', options.status)
  if (options.eventType) params.append('event_type', options.eventType)
  if (options.unreadOnly) params.append('unread_only', 'true')
  if (options.skip !== undefined) params.append('skip', options.skip.toString())
  if (options.limit !== undefined) params.append('limit', options.limit.toString())

  const queryString = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${API_BASE_URL}/notifications${queryString}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch notifications: ${response.status}`)
  }
  return response.json()
}

export async function markNotificationAsRead(token: string, notificationId: string): Promise<NotificationItem> {
  const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to mark notification as read: ${response.status}`)
  }
  return response.json()
}

export async function markAllNotificationsAsRead(token: string): Promise<{ marked_read: number }> {
  const response = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to mark all notifications as read: ${response.status}`)
  }
  return response.json()
}
