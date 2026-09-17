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

export interface DatabaseHealthCheckResponse {
  status: string
  database: string
  latency_ms: number
  timestamp: string
}
