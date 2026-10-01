/**
 * Jobs and Discovery API client service.
 */

import {
  JobDetail,
  JobListResponse,
  SavedJobListResponse,
} from '../types/job'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export interface FetchJobsOptions {
  q?: string
  location?: string
  workplace_type?: string
  employment_type?: string
  company_id?: string
  min_score?: number
  sort_by?: 'best_match' | 'newest' | 'title'
  page?: number
  page_size?: number
}

export async function fetchJobs(
  options: FetchJobsOptions = {},
  token?: string | null,
): Promise<JobListResponse> {
  const params = new URLSearchParams()
  if (options.q) params.append('q', options.q)
  if (options.location) params.append('location', options.location)
  if (options.workplace_type) params.append('workplace_type', options.workplace_type)
  if (options.employment_type) params.append('employment_type', options.employment_type)
  if (options.company_id) params.append('company_id', options.company_id)
  if (options.min_score !== undefined && !isNaN(options.min_score)) {
    params.append('min_score', options.min_score.toString())
  }
  if (options.sort_by) params.append('sort_by', options.sort_by)
  if (options.page) params.append('page', options.page.toString())
  if (options.page_size) params.append('page_size', options.page_size.toString())

  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${API_BASE_URL}/jobs${query}`, { headers })

  if (!response.ok) {
    throw new Error(`Failed to fetch jobs (${response.status})`)
  }

  return response.json()
}

export async function fetchJobDetail(
  jobId: string,
  token?: string | null,
): Promise<JobDetail> {
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, { headers })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Job opening not found.')
    }
    throw new Error(`Failed to fetch job details (${response.status})`)
  }

  return response.json()
}

export async function fetchSavedJobs(
  token: string,
  page: number = 1,
  pageSize: number = 20,
): Promise<SavedJobListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/jobs/saved?page=${page}&page_size=${pageSize}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  )

  if (!response.ok) {
    throw new Error(`Failed to fetch saved jobs (${response.status})`)
  }

  return response.json()
}

export async function saveJob(
  jobId: string,
  token: string,
  notes?: string,
): Promise<{ status: string; job_id: string; saved_id: string }> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ notes }),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to save job (${response.status})`)
  }

  return response.json()
}

export async function unsaveJob(
  jobId: string,
  token: string,
): Promise<{ status: string; job_id: string }> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/save`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to unsave job (${response.status})`)
  }

  return response.json()
}
