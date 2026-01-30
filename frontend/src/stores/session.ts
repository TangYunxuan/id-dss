import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Session,
  CourseContextForm,
  DesignStep,
  AIRecommendation,
  UserAction,
  ObjectiveAnalysisResponse,
  ActivityItem,
  DesignPhase,
} from '@/types'

export const useSessionStore = defineStore('session', () => {
  // ============ State ============
  
  // Current session
  const currentSession = ref<Session | null>(null)
  const sessionId = ref<number | null>(null)
  
  // Form data (persisted during design flow)
  const courseContext = ref<CourseContextForm>({
    course_title: '',
    level: '',
    modality: '',
    constraints: '',
    learning_objectives: '',
  })
  
  // Design steps
  const designSteps = ref<DesignStep[]>([])
  
  // AI recommendations
  const recommendations = ref<AIRecommendation[]>([])
  
  // User actions history
  const userActions = ref<UserAction[]>([])
  
  // Parsed AI responses (for UI display)
  const objectiveAnalysis = ref<ObjectiveAnalysisResponse | null>(null)
  const activitySuggestions = ref<ActivityItem[]>([])
  
  // Loading states
  const isLoading = ref(false)
  const isGenerating = ref(false)
  
  // Current phase
  const currentPhase = ref<DesignPhase>('context')

  // ============ Getters ============
  
  const hasActiveSession = computed(() => sessionId.value !== null)
  
  const currentStepForPhase = computed(() => (phase: string) => {
    return designSteps.value.find(step => step.phase === phase)
  })
  
  const recommendationsForStep = computed(() => (stepId: number) => {
    return recommendations.value.filter(rec => rec.step_id === stepId)
  })

  // ============ Actions ============
  
  function setSession(session: Session) {
    currentSession.value = session
    sessionId.value = session.id
  }
  
  function setCourseContext(context: CourseContextForm) {
    courseContext.value = { ...context }
  }

  function updateLearningObjectives(objectives: string) {
    courseContext.value.learning_objectives = objectives
  }
  
  function setCurrentPhase(phase: DesignPhase) {
    currentPhase.value = phase
  }
  
  function addDesignStep(step: DesignStep) {
    designSteps.value.push(step)
  }
  
  function addRecommendation(recommendation: AIRecommendation) {
    recommendations.value.push(recommendation)
  }
  
  function setObjectiveAnalysis(analysis: ObjectiveAnalysisResponse) {
    objectiveAnalysis.value = analysis
  }
  
  function setActivitySuggestions(suggestions: ActivityItem[]) {
    activitySuggestions.value = suggestions
  }
  
  function addUserAction(action: UserAction) {
    userActions.value.push(action)
  }
  
  function setLoading(loading: boolean) {
    isLoading.value = loading
  }
  
  function setGenerating(generating: boolean) {
    isGenerating.value = generating
  }
  
  function resetSession() {
    currentSession.value = null
    sessionId.value = null
    courseContext.value = {
      course_title: '',
      level: '',
      modality: '',
      constraints: '',
      learning_objectives: '',
    }
    designSteps.value = []
    recommendations.value = []
    userActions.value = []
    objectiveAnalysis.value = null
    activitySuggestions.value = []
    currentPhase.value = 'context'
    isLoading.value = false
    isGenerating.value = false
  }

  return {
    // State
    currentSession,
    sessionId,
    courseContext,
    designSteps,
    recommendations,
    userActions,
    objectiveAnalysis,
    activitySuggestions,
    isLoading,
    isGenerating,
    currentPhase,
    
    // Getters
    hasActiveSession,
    currentStepForPhase,
    recommendationsForStep,
    
    // Actions
    setSession,
    setCourseContext,
    updateLearningObjectives,
    setCurrentPhase,
    addDesignStep,
    addRecommendation,
    setObjectiveAnalysis,
    setActivitySuggestions,
    addUserAction,
    setLoading,
    setGenerating,
    resetSession,
  }
})

