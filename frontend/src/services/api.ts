/**
 * Resilient API service layer for communicating with the JobWatch AI backend.
 * Provides timeout protection, standard error extraction, and correlation IDs.
 */

import { DatabaseHealthCheckResponse, HealthCheckResponse } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const DEFAULT_TIMEOUT_MS = 15000

/**
 * Resilient fetch wrapper with timeout and standard error extraction.
 */
export async function resilientFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(input, {
      ...init,
      signal: init?.signal || controller.signal,
    })
    return response
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s. Please check your network or try again.`)
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const response = await resilientFetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`)
  }
  return response.json()
}

export async function fetchDbHealth(): Promise<DatabaseHealthCheckResponse> {
  const response = await resilientFetch(`${API_BASE_URL}/health/db`)
  if (!response.ok) {
    throw new Error(`Database health check failed with status: ${response.status}`)
  }
  return response.json()
}
