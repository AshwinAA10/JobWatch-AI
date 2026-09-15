/**
 * Backend API response types for JobWatch AI.
 */

export interface HealthCheckResponse {
  status: string
  app_name: string
  version: string
  environment: string
  timestamp: string
}
