/**
 * Matching and scoring types for JobWatch AI.
 */

export interface MatchBreakdown {
  skills?: number
  experience?: number
  education?: number
  location?: number
  workplace?: number
  employment_type?: number
  salary?: number
  semantic_fit?: number
  [key: string]: number | undefined
}

export interface MatchResult {
  score: number
  scoring_version: string
  breakdown: MatchBreakdown
  matched_criteria: string[]
  missing_criteria: string[]
  mismatches: string[]
  reasons: string[]
}
