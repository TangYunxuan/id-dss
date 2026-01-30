/**
 * Type definitions for ID-DSS application
 */

// ============ Session Types ============

export interface Session {
  id: number
  course_title: string
  level: string
  modality: string
  constraints: string | null
  learning_objectives: string | null
  created_at: string
}

export interface SessionCreate {
  course_title: string
  level: string
  modality: string
  constraints?: string
  learning_objectives?: string
}

// ============ Design Step Types ============

export interface DesignStep {
  id: number
  session_id: number
  phase: string
  user_input: string | null
  created_at: string
}

export interface DesignStepCreate {
  session_id: number
  phase: string
  user_input?: string
}

// ============ AI Recommendation Types ============

export interface AIRecommendation {
  id: number
  step_id: number
  phase: string
  raw_response: string
  created_at: string
}

export interface AIRecommendationCreate {
  step_id: number
  phase: string
  raw_response: string
}

// ============ User Action Types ============

export type ActionType = 'accept' | 'reject' | 'edit' | 'comment' | 'regenerate'

export interface UserAction {
  id: number
  step_id: number
  recommendation_id: number | null
  action_type: ActionType
  edited_content: string | null
  comment: string | null
  created_at: string
}

export interface UserActionCreate {
  step_id: number
  recommendation_id?: number
  action_type: ActionType
  edited_content?: string
  comment?: string
}

// ============ Form Types ============

export interface CourseContextForm {
  course_title: string
  level: string
  modality: string
  constraints: string
  learning_objectives: string
}

// ============ AI Response Types (Parsed) ============

export interface BloomAnalysisItem {
  objective: string
  current_level: string
  domain: string
  is_measurable: boolean
  suggestion: string
}

export interface ObjectiveAnalysisResponse {
  overall_assessment: string
  bloom_analysis: BloomAnalysisItem[]
  alignment_notes: string
  missing_coverage: string[]
  improved_objectives: string[]
}

export interface ActivityItem {
  title: string
  type: string
  description: string
  objective_alignment: string[]
  duration: string
  materials_needed: string[]
  instructions: string[]
  assessment_criteria: string
  adaptations: {
    online: string
    accessibility: string
  }
}

export interface ActivitySuggestionResponse {
  activities: ActivityItem[]
  sequence_rationale: string
  total_estimated_time: string
}

export interface AssessmentItem {
  title: string
  type: string
  method: string
  description: string
  objective_alignment: string[]
  timing: string
  weight: string
  rubric_criteria: string[]
  feedback_strategy: string
}

export interface AssessmentRecommendationResponse {
  assessments: AssessmentItem[]
  assessment_strategy_rationale: string
  formative_summative_balance: string
}

// ============ UI State Types ============

export type DesignPhase = 
  | 'context' 
  | 'objective-analysis' 
  | 'activity-suggestion' 
  | 'summary'

export interface StepProgress {
  phase: DesignPhase
  completed: boolean
  active: boolean
}

// ============ LLM Status ============

export interface LLMStatus {
  provider: string
  model: string
  configured: boolean
  message: string
}
