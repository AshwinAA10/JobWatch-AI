/**
 * Notification and alerting types for JobWatch AI Phase 8.
 */

export type NotificationType = 'NEW_MATCH' | 'HIGH_QUALITY_MATCH' | 'MONITORING_FAILURE'
export type NotificationStatus = 'PENDING' | 'SENT' | 'FAILED'
export type DeliveryStatus = 'PENDING' | 'PROCESSING' | 'SENT' | 'RETRYING' | 'FAILED' | 'CANCELLED'

export interface NotificationPreference {
  id: string
  profile_id: string
  email_enabled: boolean
  webhook_enabled: boolean
  webhook_url?: string | null
  minimum_match_score: number
  frequency: 'IMMEDIATE' | 'DAILY_DIGEST'
  max_per_hour: number
  created_at: string
  updated_at: string
}

export interface NotificationPreferenceUpdate {
  email_enabled?: boolean
  webhook_enabled?: boolean
  webhook_url?: string | null
  webhook_secret?: string | null
  minimum_match_score?: number
  frequency?: 'IMMEDIATE' | 'DAILY_DIGEST'
  max_per_hour?: number
}

export interface NotificationDelivery {
  id: string
  notification_id: string
  channel: 'EMAIL' | 'WEBHOOK'
  status: DeliveryStatus
  attempt_count: number
  max_attempts: number
  provider_message_id?: string | null
  last_error?: string | null
  next_retry_at?: string | null
  sent_at?: string | null
  created_at: string
  updated_at: string
}

export interface NotificationItem {
  id: string
  profile_id: string
  event_type: NotificationType
  job_id: string
  match_id?: string | null
  title: string
  body: string
  status: NotificationStatus
  is_read: boolean
  read_at?: string | null
  payload: Record<string, any>
  deliveries: NotificationDelivery[]
  created_at: string
  updated_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  total: number
  skip: number
  limit: number
  unread_count: number
}
