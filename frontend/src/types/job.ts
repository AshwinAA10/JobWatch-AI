/**
 * Job and Discovery types for JobWatch AI Phase 9.
 */

export interface JobCard {
  id: string
  company_id: string
  company_name: string
  company_slug: string
  career_source_name?: string | null
  title: string
  location?: string | null
  employment_type?: string | null
  workplace_type?: string | null
  application_url?: string | null
  posted_at?: string | null
  first_seen_at: string
  canonical_job_id?: string | null
  is_active: boolean
  match_score?: number | null
  match_confidence?: string | null
  match_type?: string | null
  match_reasons?: string[]
  is_saved: boolean
  application_id?: string | null
  application_status?: string | null
}

export interface AIExplanationData {
  summary: string
  strengths: string[]
  gaps: string[]
  recommendation: string
}

export interface StructuredRequirements {
  required_skills?: string[]
  preferred_skills?: string[]
  minimum_years_experience?: number
  education_level?: string
  responsibilities?: string[]
  qualifications?: string[]
}

export interface JobDetail extends JobCard {
  description?: string | null
  source_url?: string | null
  matched_criteria?: string[]
  missing_criteria?: string[]
  breakdown?: Record<string, number | any> | null
  ai_explanation?: AIExplanationData | null
  structured_requirements?: StructuredRequirements | null
  duplicate_count: number
}

export interface JobListResponse {
  items: JobCard[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SavedJobItem {
  id: string
  profile_id: string
  job_id: string
  notes?: string | null
  created_at: string
  job: JobCard
}

export interface SavedJobListResponse {
  items: SavedJobItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface JobFiltersState {
  q: string
  location: string
  workplace_type: string
  employment_type: string
  min_match: string
  sort_by: 'best_match' | 'newest' | 'title'
  page: number
  page_size: number
}
