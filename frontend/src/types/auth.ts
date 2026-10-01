/**
 * Authentication and user identity types for JobWatch AI.
 */

export interface User {
  id: string
  email: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in_seconds: number
}

export interface UserLoginRequest {
  email: string
  password: string
}

export interface UserRegisterRequest {
  email: string
  password: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}
