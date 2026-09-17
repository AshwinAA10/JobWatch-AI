/**
 * API service layer for communicating with the JobWatch AI backend.
 */

import { DatabaseHealthCheckResponse, HealthCheckResponse } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`)
  }
  return response.json()
}

export async function fetchDbHealth(): Promise<DatabaseHealthCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/health/db`)
  if (!response.ok) {
    throw new Error(`Database health check failed with status: ${response.status}`)
  }
  return response.json()
}
