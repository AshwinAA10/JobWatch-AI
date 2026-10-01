/**
 * Application Tracking and Lifecycle types for JobWatch AI Phase 10.
 */

export type ApplicationStatus =
  | 'APPLIED'
  | 'SCREENING'
  | 'INTERVIEW'
  | 'OFFER'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'ACCEPTED'

export type InterviewType =
  | 'PHONE'
  | 'TECHNICAL'
  | 'HR'
  | 'BEHAVIORAL'
  | 'MANAGERIAL'
  | 'FINAL'
  | 'OTHER'

export type InterviewStatus =
  | 'SCHEDULED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'RESCHEDULED'

export interface ApplicationHistoryItem {
  id: string
  application_id: string
  old_status?: ApplicationStatus | string | null
  new_status: ApplicationStatus | string
  changed_at: string
  note?: string | null
  created_at: string
}

export interface ApplicationNoteItem {
  id: string
  application_id: string
  content: string
  created_at: string
  updated_at: string
}

export interface InterviewItem {
  id: string
  application_id: string
  interview_type: InterviewType | string
  status: InterviewStatus | string
  scheduled_at: string
  duration_minutes?: number | null
  interviewer_names?: string | null
  location?: string | null
  meeting_url?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface ApplicationListItem {
  id: string
  profile_id: string
  job_id?: string | null
  status: ApplicationStatus | string
  applied_at: string
  last_status_changed_at: string
  company_name: string
  job_title: string
  job_location?: string | null
  external_application_url?: string | null
  match_score_at_application?: number | null
  notes_count: number
  interviews_count: number
  created_at: string
  updated_at: string
}

export interface ApplicationDetail {
  id: string
  profile_id: string
  job_id?: string | null
  status: ApplicationStatus | string
  applied_at: string
  last_status_changed_at: string
  company_name: string
  job_title: string
  job_location?: string | null
  external_application_url?: string | null
  match_score_at_application?: number | null
  notes?: string | null
  created_at: string
  updated_at: string
  history: ApplicationHistoryItem[]
  application_notes: ApplicationNoteItem[]
  interviews: InterviewItem[]
}

export interface ApplicationListResponse {
  items: ApplicationListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApplicationStats {
  total: number
  applied: number
  screening: number
  interview: number
  offer: number
  rejected: number
  withdrawn: number
  accepted: number
}

export interface ApplicationCreatePayload {
  job_id?: string | null
  company_name?: string | null
  job_title?: string | null
  job_location?: string | null
  external_application_url?: string | null
  applied_at?: string | null
  notes?: string | null
}

export interface ApplicationStatusUpdatePayload {
  status: ApplicationStatus
  note?: string | null
}

export interface ApplicationNoteCreatePayload {
  content: string
}

export interface InterviewCreatePayload {
  interview_type: InterviewType
  status?: InterviewStatus
  scheduled_at: string
  duration_minutes?: number | null
  interviewer_names?: string | null
  location?: string | null
  meeting_url?: string | null
  notes?: string | null
}
