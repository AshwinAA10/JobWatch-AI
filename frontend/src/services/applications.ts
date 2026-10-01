/**
 * Application Tracking and Lifecycle API client service for JobWatch AI Phase 10.
 */

import {
  ApplicationCreatePayload,
  ApplicationDetail,
  ApplicationHistoryItem,
  ApplicationListResponse,
  ApplicationNoteCreatePayload,
  ApplicationNoteItem,
  ApplicationStats,
  ApplicationStatusUpdatePayload,
  InterviewCreatePayload,
  InterviewItem,
} from '../types/application'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export interface FetchApplicationsOptions {
  status?: string
  company?: string
  q?: string
  sort_by?: 'newest' | 'oldest' | 'recently_updated' | 'company'
  page?: number
  page_size?: number
}

function authHeaders(token: string, extra?: Record<string, string>): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    ...(extra || {}),
  }
}

export async function fetchApplications(
  token: string,
  options: FetchApplicationsOptions = {},
): Promise<ApplicationListResponse> {
  const params = new URLSearchParams()
  if (options.status) params.append('status', options.status)
  if (options.company) params.append('company', options.company)
  if (options.q) params.append('q', options.q)
  if (options.sort_by) params.append('sort_by', options.sort_by)
  if (options.page) params.append('page', options.page.toString())
  if (options.page_size) params.append('page_size', options.page_size.toString())

  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${API_BASE_URL}/applications${query}`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch applications (${response.status})`)
  }

  return response.json()
}

export async function fetchApplicationStats(token: string): Promise<ApplicationStats> {
  const response = await fetch(`${API_BASE_URL}/applications/stats`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch application statistics (${response.status})`)
  }

  return response.json()
}

export async function fetchApplicationDetail(
  token: string,
  id: string,
): Promise<ApplicationDetail> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Application not found or unauthorized.')
    }
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch application (${response.status})`)
  }

  return response.json()
}

export async function createApplication(
  token: string,
  payload: ApplicationCreatePayload,
): Promise<ApplicationDetail> {
  const response = await fetch(`${API_BASE_URL}/applications`, {
    method: 'POST',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to track application (${response.status})`)
  }

  return response.json()
}

export async function updateApplicationStatus(
  token: string,
  id: string,
  payload: ApplicationStatusUpdatePayload,
): Promise<ApplicationDetail> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/status`, {
    method: 'PATCH',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update status (${response.status})`)
  }

  return response.json()
}

export async function deleteApplication(token: string, id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to delete application (${response.status})`)
  }
}

export async function fetchApplicationHistory(
  token: string,
  id: string,
): Promise<ApplicationHistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/history`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch application history (${response.status})`)
  }

  return response.json()
}

export async function fetchApplicationNotes(
  token: string,
  id: string,
): Promise<ApplicationNoteItem[]> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/notes`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch notes (${response.status})`)
  }

  return response.json()
}

export async function createApplicationNote(
  token: string,
  id: string,
  payload: ApplicationNoteCreatePayload,
): Promise<ApplicationNoteItem> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/notes`, {
    method: 'POST',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to create note (${response.status})`)
  }

  return response.json()
}

export async function deleteApplicationNote(
  token: string,
  id: string,
  noteId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/notes/${noteId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to delete note (${response.status})`)
  }
}

export async function fetchInterviews(
  token: string,
  id: string,
): Promise<InterviewItem[]> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/interviews`, {
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch interviews (${response.status})`)
  }

  return response.json()
}

export async function createInterview(
  token: string,
  id: string,
  payload: InterviewCreatePayload,
): Promise<InterviewItem> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/interviews`, {
    method: 'POST',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to schedule interview (${response.status})`)
  }

  return response.json()
}

export async function updateInterview(
  token: string,
  id: string,
  interviewId: string,
  payload: Partial<InterviewCreatePayload>,
): Promise<InterviewItem> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/interviews/${interviewId}`, {
    method: 'PATCH',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update interview (${response.status})`)
  }

  return response.json()
}

export async function deleteInterview(
  token: string,
  id: string,
  interviewId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}/interviews/${interviewId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to delete interview (${response.status})`)
  }
}
