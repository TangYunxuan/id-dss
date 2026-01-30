/**
 * API Service - handles all backend communication
 * 
 * Base URL is proxied through Vite to avoid CORS issues in development
 */

import axios from 'axios'
import type {
  Session,
  SessionCreate,
  DesignStep,
  DesignStepCreate,
  AIRecommendation,
  UserAction,
  UserActionCreate,
} from '@/types'

// In dev, Vite proxies /api -> http://localhost:8000
// In production (GitHub Pages), set VITE_API_BASE_URL to your Render (or custom) API base:
// e.g. VITE_API_BASE_URL="https://api.tangyunxaun.com/api/v1"
const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  (import.meta.env.VITE_API_URL as string | undefined) || // backward/alt name if you prefer
  '/api/v1'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ============ Session Endpoints ============

/**
 * Create a new design session
 */
export async function createSession(data: SessionCreate): Promise<Session> {
  const response = await api.post<Session>('/sessions/', data)
  return response.data
}

export async function updateSession(sessionId: number, data: Partial<SessionCreate>): Promise<Session> {
  const response = await api.patch<Session>(`/sessions/${sessionId}`, data)
  return response.data
}

/**
 * Get a session by ID
 */
export async function getSession(sessionId: number): Promise<Session> {
  const response = await api.get<Session>(`/sessions/${sessionId}`)
  return response.data
}

/**
 * List all sessions
 */
export async function listSessions(): Promise<Session[]> {
  const response = await api.get<Session[]>('/sessions/')
  return response.data
}

// ============ Design Step Endpoints ============

/**
 * Create a new design step
 */
export async function createStep(data: DesignStepCreate): Promise<DesignStep> {
  const response = await api.post<DesignStep>('/steps/', data)
  return response.data
}

/**
 * Get steps for a session
 */
export async function getStepsForSession(sessionId: number): Promise<DesignStep[]> {
  const response = await api.get<DesignStep[]>('/steps/', {
    params: { session_id: sessionId },
  })
  return response.data
}

/**
 * Get a step by ID
 */
export async function getStep(stepId: number): Promise<DesignStep> {
  const response = await api.get<DesignStep>(`/steps/${stepId}`)
  return response.data
}

// ============ Recommendation Endpoints ============

/**
 * Get recommendations for a step
 */
export async function getRecommendationsForStep(stepId: number): Promise<AIRecommendation[]> {
  const response = await api.get<AIRecommendation[]>('/recommendations/', {
    params: { step_id: stepId },
  })
  return response.data
}

/**
 * Get a recommendation by ID
 */
export async function getRecommendation(recommendationId: number): Promise<AIRecommendation> {
  const response = await api.get<AIRecommendation>(`/recommendations/${recommendationId}`)
  return response.data
}

// ============ User Action Endpoints ============

/**
 * Create a user action (accept, reject, edit, etc.)
 */
export async function createAction(data: UserActionCreate): Promise<UserAction> {
  const response = await api.post<UserAction>('/actions/', data)
  return response.data
}

/**
 * Get actions for a step
 */
export async function getActionsForStep(stepId: number): Promise<UserAction[]> {
  const response = await api.get<UserAction[]>('/actions/', {
    params: { step_id: stepId },
  })
  return response.data
}

// ============ LLM Endpoints ============

export interface LLMResponse {
  success: boolean
  step_id: number
  recommendation_id: number
  data: Record<string, unknown>
}

export interface LLMStatus {
  provider: string
  model: string
  configured: boolean
  message: string
}

/**
 * Check LLM configuration status
 */
export async function getLLMStatus(): Promise<LLMStatus> {
  const response = await api.get<LLMStatus>('/llm/status')
  return response.data
}

/**
 * Run objective analysis using AI
 */
export async function analyzeObjectives(
  sessionId: number,
  objectives: string
): Promise<LLMResponse> {
  const response = await api.post<LLMResponse>('/llm/analyze-objectives', {
    session_id: sessionId,
    objectives: objectives,
  })
  return response.data
}

/**
 * Generate activity suggestions using AI
 */
export async function suggestActivities(
  sessionId: number,
  objectives: string
): Promise<LLMResponse> {
  const response = await api.post<LLMResponse>('/llm/suggest-activities', {
    session_id: sessionId,
    objectives: objectives,
  })
  return response.data
}

/**
 * Generate assessment recommendations using AI
 */
export async function recommendAssessments(
  sessionId: number,
  objectives: string,
  activities: string
): Promise<LLMResponse> {
  const response = await api.post<LLMResponse>('/llm/recommend-assessments', {
    session_id: sessionId,
    objectives: objectives,
    activities: activities,
  })
  return response.data
}

// ============ Export Endpoints ============

export interface ExportData {
  session: Session
  design_steps: Array<{
    id: number
    phase: string
    user_input: string | null
    created_at: string
    recommendations: Array<{
      id: number
      phase: string
      response: Record<string, unknown>
      created_at: string
    }>
    user_actions: Array<{
      id: number
      recommendation_id: number | null
      action_type: string
      edited_content: string | null
      comment: string | null
      created_at: string
    }>
  }>
  summary: {
    total_steps: number
    total_recommendations: number
    total_actions: number
    actions_by_type: Record<string, number>
  }
  exported_at: string
}

/**
 * Export complete session data from backend
 */
export async function exportSession(sessionId: number): Promise<ExportData> {
  const response = await api.get<ExportData>(`/export/${sessionId}`)
  return response.data
}

/**
 * Download session export as Word (DOCX)
 */
export async function downloadSessionExportDocx(sessionId: number): Promise<void> {
  const response = await api.get(`/export/${sessionId}/docx`, {
    responseType: 'blob',
  })

  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `id-dss-session-${sessionId}-${new Date().toISOString().split('T')[0]}.docx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Download session export as PDF
 */
export async function downloadSessionExportPdf(sessionId: number): Promise<void> {
  const response = await api.get(`/export/${sessionId}/pdf`, {
    responseType: 'blob',
  })

  const blob = new Blob([response.data], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `id-dss-session-${sessionId}-${new Date().toISOString().split('T')[0]}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// ============ Health Check ============

/**
 * Check if the backend is available
 */
export async function healthCheck(): Promise<{ status: string }> {
  const response = await api.get<{ status: string }>('/health')
  return response.data
}

export default api
