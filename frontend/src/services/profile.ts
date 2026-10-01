/**
 * Candidate profile, skills, experience, and preferences service.
 */

import {
  CandidatePreferences,
  CandidatePreferencesUpdate,
  CandidateProfile,
  CandidateProfileUpdate,
  CandidateSkill,
  CandidateSkillCreate,
  Education,
  EducationCreate,
  Experience,
  ExperienceCreate,
} from '../types/profile'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export async function fetchCandidateProfile(token: string): Promise<CandidateProfile> {
  const response = await fetch(`${API_BASE_URL}/profile`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to load profile (${response.status})`)
  }

  return response.json()
}

export async function updateCandidateProfile(
  token: string,
  update: CandidateProfileUpdate,
): Promise<CandidateProfile> {
  const response = await fetch(`${API_BASE_URL}/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(update),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to update profile (${response.status})`)
  }

  return response.json()
}

export async function fetchCandidatePreferences(token: string): Promise<CandidatePreferences> {
  const response = await fetch(`${API_BASE_URL}/profile/preferences`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to load preferences (${response.status})`)
  }

  return response.json()
}

export async function updateCandidatePreferences(
  token: string,
  update: CandidatePreferencesUpdate,
): Promise<CandidatePreferences> {
  const response = await fetch(`${API_BASE_URL}/profile/preferences`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(update),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to update preferences (${response.status})`)
  }

  return response.json()
}

export async function addCandidateSkill(
  token: string,
  skill: CandidateSkillCreate,
): Promise<CandidateSkill> {
  const response = await fetch(`${API_BASE_URL}/profile/skills`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(skill),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to add skill (${response.status})`)
  }

  return response.json()
}

export async function removeCandidateSkill(token: string, skillId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/profile/skills/${skillId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to remove skill (${response.status})`)
  }
}

export async function addExperience(
  token: string,
  experience: ExperienceCreate,
): Promise<Experience> {
  const response = await fetch(`${API_BASE_URL}/profile/experience`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(experience),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to add experience (${response.status})`)
  }

  return response.json()
}

export async function removeExperience(token: string, experienceId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/profile/experience/${experienceId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to remove experience (${response.status})`)
  }
}

export async function addEducation(
  token: string,
  education: EducationCreate,
): Promise<Education> {
  const response = await fetch(`${API_BASE_URL}/profile/education`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(education),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Failed to add education (${response.status})`)
  }

  return response.json()
}

export async function removeEducation(token: string, educationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/profile/education/${educationId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to remove education (${response.status})`)
  }
}
