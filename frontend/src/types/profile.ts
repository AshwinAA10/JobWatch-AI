/**
 * Candidate profile, skills, experience, education, and preferences types.
 */

export type ProficiencyLevel = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT'
export type ProfileVisibility = 'PRIVATE' | 'PUBLIC' | 'ANONYMOUS'
export type WorkplaceType = 'REMOTE' | 'HYBRID' | 'ONSITE'
export type EmploymentType = 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'INTERNSHIP'

export interface CandidateSkill {
  id: string
  profile_id: string
  skill_id: string
  skill_name: string
  proficiency: ProficiencyLevel
  years_experience?: number | null
  created_at: string
}

export interface CandidateSkillCreate {
  skill_name: string
  proficiency?: ProficiencyLevel
  years_experience?: number | null
}

export interface Experience {
  id: string
  profile_id: string
  company_name: string
  job_title: string
  description?: string | null
  location?: string | null
  employment_type?: string | null
  start_date: string
  end_date?: string | null
  is_current: boolean
  created_at: string
}

export interface ExperienceCreate {
  company_name: string
  job_title: string
  description?: string | null
  location?: string | null
  employment_type?: string | null
  start_date: string
  end_date?: string | null
  is_current: boolean
}

export interface Education {
  id: string
  profile_id: string
  institution_name: string
  degree: string
  field_of_study?: string | null
  start_date?: string | null
  end_date?: string | null
  grade?: string | null
  created_at: string
}

export interface EducationCreate {
  institution_name: string
  degree: string
  field_of_study?: string | null
  start_date?: string | null
  end_date?: string | null
  grade?: string | null
}

export interface CandidatePreferences {
  id: string
  profile_id: string
  desired_titles: string[]
  preferred_locations: string[]
  workplace_types: string[]
  employment_types: string[]
  minimum_salary?: number | null
  maximum_salary?: number | null
  salary_currency: string
  minimum_experience_years?: number | null
  maximum_experience_years?: number | null
  willing_to_relocate: boolean
  remote_preference?: string | null
  created_at: string
  updated_at: string
}

export interface CandidatePreferencesUpdate {
  desired_titles?: string[]
  preferred_locations?: string[]
  workplace_types?: string[]
  employment_types?: string[]
  minimum_salary?: number | null
  maximum_salary?: number | null
  salary_currency?: string
  minimum_experience_years?: number | null
  maximum_experience_years?: number | null
  willing_to_relocate?: boolean
  remote_preference?: string | null
}

export interface CandidateProfile {
  id: string
  user_id: string
  first_name?: string | null
  last_name?: string | null
  headline?: string | null
  bio?: string | null
  phone?: string | null
  city?: string | null
  state?: string | null
  country?: string | null
  years_of_experience?: number | null
  current_job_title?: string | null
  current_company?: string | null
  highest_education_level?: string | null
  profile_visibility: ProfileVisibility
  profile_completion_percent: number
  skills: CandidateSkill[]
  experiences: Experience[]
  educations: Education[]
  preferences?: CandidatePreferences | null
  created_at: string
  updated_at: string
}

export interface CandidateProfileUpdate {
  first_name?: string | null
  last_name?: string | null
  headline?: string | null
  bio?: string | null
  phone?: string | null
  city?: string | null
  state?: string | null
  country?: string | null
  years_of_experience?: number | null
  current_job_title?: string | null
  current_company?: string | null
  highest_education_level?: string | null
  profile_visibility?: ProfileVisibility
}
