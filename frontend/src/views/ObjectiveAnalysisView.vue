<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { analyzeObjectives, getLLMStatus, createAction, updateSession } from '@/services/api'
import type { ObjectiveAnalysisResponse, LLMStatus } from '@/types'
import { stripMarkdown } from '@/utils/text'

const router = useRouter()
const sessionStore = useSessionStore()

const isAnalyzing = ref(false)
const llmStatus = ref<LLMStatus | null>(null)
const analysisResult = ref<ObjectiveAnalysisResponse | null>(null)
const stepId = ref<number | null>(null)
const recommendationId = ref<number | null>(null)
const errorMessage = ref('')
const objectivesDraft = ref('')
// Tracks the last objectives text successfully persisted to backend (or initial baseline on mount).
// This is used for "dirty" detection so the Save button reflects real unsaved changes.
const lastSavedObjectives = ref('')
const hasSavedBaseline = ref(false)
const successMessage = ref('')
const objectivesTextarea = ref<HTMLTextAreaElement | null>(null)
const isSaving = ref(false)

const hasObjectives = computed(() => {
  return objectivesDraft.value.trim().length > 0
})

const isDirty = computed(() => {
  return (objectivesDraft.value || '') !== (lastSavedObjectives.value || '')
})

onMounted(async () => {
  // Redirect if no session
  if (!sessionStore.hasActiveSession) {
    router.push('/new-session')
    return
  }
  
  // Check LLM status
  try {
    llmStatus.value = await getLLMStatus()
  } catch (error) {
    console.error('Failed to get LLM status:', error)
  }
})

watch(
  () => sessionStore.courseContext.learning_objectives,
  (val) => {
    const next = val || ''

    // First hydration: establish baseline + draft from store.
    if (!hasSavedBaseline.value) {
      objectivesDraft.value = next
      lastSavedObjectives.value = next
      hasSavedBaseline.value = true
      return
    }

    // If user hasn't made edits since last save, keep draft in sync when navigating back/forth.
    if (!isDirty.value) {
      objectivesDraft.value = next
    }
  },
  { immediate: true }
)

async function runAnalysis() {
  if (!sessionStore.sessionId) return
  
  isAnalyzing.value = true
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    // Always keep store updated for downstream steps.
    sessionStore.updateLearningObjectives(objectivesDraft.value)

    // Persist to backend so refresh/navigation doesn't lose it.
    // If it fails, still allow analysis to run, but keep "dirty" state so user can retry saving.
    try {
      await updateSession(sessionStore.sessionId, { learning_objectives: objectivesDraft.value })
      lastSavedObjectives.value = objectivesDraft.value
    } catch (e) {
      console.warn('Failed to persist objectives before analysis:', e)
    }

    const result = await analyzeObjectives(
      sessionStore.sessionId,
      objectivesDraft.value
    )
    
    stepId.value = result.step_id
    recommendationId.value = result.recommendation_id
    analysisResult.value = result.data as unknown as ObjectiveAnalysisResponse
    
    // Store in session
    sessionStore.addDesignStep({
      id: result.step_id,
      session_id: sessionStore.sessionId,
      phase: 'objective-analysis',
      user_input: objectivesDraft.value,
      created_at: new Date().toISOString(),
    })
    
  } catch (error: unknown) {
    console.error('Analysis failed:', error)
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      errorMessage.value = axiosError.response?.data?.detail || 'Analysis failed. Please try again.'
    } else {
      errorMessage.value = 'Analysis failed. Please try again.'
    }
  } finally {
    isAnalyzing.value = false
  }
}

function getImprovedObjectivesText(): string {
  if (!analysisResult.value?.improved_objectives?.length) return ''
  return analysisResult.value.improved_objectives.join('\n')
}

async function copyText(text: string, successText: string) {
  const cleaned = stripMarkdown(text)
  try {
    await navigator.clipboard.writeText(cleaned)
    successMessage.value = successText
  } catch (e) {
    console.warn('Failed to copy to clipboard:', e)
    successMessage.value = 'Could not access clipboard. Please copy manually.'
  }
}

async function persistObjectives(updated: string, actionComment: string) {
  sessionStore.updateLearningObjectives(updated)
  if (sessionStore.sessionId) {
    // Don't swallow save errors here — callers (Save button, replace/insert helpers) need to know.
    const session = await updateSession(sessionStore.sessionId, { learning_objectives: updated })
    lastSavedObjectives.value = session.learning_objectives ?? updated
  }
  if (stepId.value) {
    try {
      await createAction({
        step_id: stepId.value,
        recommendation_id: recommendationId.value ?? undefined,
        action_type: 'edit',
        edited_content: updated,
        comment: actionComment,
      })
    } catch (e) {
      console.warn('Failed to record user action:', e)
    }
  }
}

async function saveObjectives() {
  if (!sessionStore.sessionId) return
  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const updated = objectivesDraft.value
    await persistObjectives(updated, 'Saved objectives edits')
    successMessage.value = 'Saved.'
  } catch (e) {
    console.warn('Failed to save objectives:', e)
    errorMessage.value = 'Save failed. Please try again.'
  } finally {
    isSaving.value = false
  }
}

async function insertImprovedObjectives() {
  const improvedRaw = getImprovedObjectivesText()
  if (!improvedRaw) return

  const improved = stripMarkdown(improvedRaw)
  const base = objectivesDraft.value.trim()
  const updated = base ? `${base}\n\n${improved}` : improved

  objectivesDraft.value = updated
  successMessage.value = 'Inserted improved objectives below your original text.'
  await persistObjectives(updated, 'Inserted suggested improved objectives (cleaned markdown)')
  await nextTick()
  objectivesTextarea.value?.focus()
}

async function replaceWithImprovedObjectives() {
  const improvedRaw = getImprovedObjectivesText()
  if (!improvedRaw) return

  const updated = stripMarkdown(improvedRaw)

  objectivesDraft.value = updated
  successMessage.value = 'Applied improved objectives. You can edit further and re-run analysis.'
  await persistObjectives(updated, 'Replaced objectives with suggested improved objectives (cleaned markdown)')

  await nextTick()
  objectivesTextarea.value?.focus()
}

async function copyImprovedObjectives() {
  const improvedRaw = getImprovedObjectivesText()
  if (!improvedRaw) return
  await copyText(improvedRaw, 'Copied improved objectives to clipboard (cleaned markdown).')
}

function proceedToActivities() {
  sessionStore.setCurrentPhase('activity-suggestion')
  router.push('/activity-suggestion')
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Page header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-surface-900 mb-2">Objective Analysis</h1>
      <p class="text-surface-600">
        Review your learning objectives and get AI-powered analysis and suggestions.
      </p>
    </div>

    <!-- LLM Status Banner -->
    <div v-if="llmStatus && !llmStatus.configured" class="mb-6 p-4 rounded-lg bg-amber-50 border border-amber-200">
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <div class="font-medium text-amber-800">LLM Not Configured</div>
          <p class="text-sm text-amber-700 mt-1">{{ llmStatus.message }}</p>
        </div>
      </div>
    </div>

    <!-- Session context card -->
    <div class="card p-6 mb-6">
      <h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">Session Context</h2>
      
      <div class="grid sm:grid-cols-3 gap-4 mb-6">
        <div>
          <div class="text-xs text-surface-500 mb-1">Course</div>
          <div class="font-medium text-surface-900">{{ sessionStore.courseContext.course_title }}</div>
        </div>
        <div>
          <div class="text-xs text-surface-500 mb-1">Level</div>
          <div class="font-medium text-surface-900 capitalize">{{ sessionStore.courseContext.level?.replace('-', ' ') }}</div>
        </div>
        <div>
          <div class="text-xs text-surface-500 mb-1">Modality</div>
          <div class="font-medium text-surface-900 capitalize">{{ sessionStore.courseContext.modality?.replace('-', ' ') }}</div>
        </div>
      </div>

      <!-- Learning objectives -->
      <div>
        <div class="flex items-center justify-between gap-3 mb-2">
          <div class="text-xs text-surface-500">Learning Objectives (editable)</div>
          <button
            class="btn-secondary"
            :disabled="!sessionStore.sessionId || isSaving || !isDirty"
            @click="saveObjectives"
          >
            <span>{{ isSaving ? 'Saving...' : 'Save' }}</span>
          </button>
        </div>
        <textarea
          v-model="objectivesDraft"
          ref="objectivesTextarea"
          rows="6"
          class="w-full bg-surface-50 rounded-lg p-4 text-sm text-surface-700 border border-surface-200 focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-300"
          placeholder="Paste or type your learning objectives here (one per line)."
        />
        <p class="text-xs text-surface-500 mt-2">
          Tip: after you get “Suggested Improvements”, you can apply them back into this box and re-run analysis.
        </p>
      </div>
    </div>

    <!-- Analysis section -->
    <div class="card p-6 mb-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="font-semibold text-surface-900">AI Objective Analysis</h2>
          <p class="text-sm text-surface-500 mt-1">
            Get feedback on objective clarity, alignment with Bloom's taxonomy, and improvement suggestions.
          </p>
        </div>
        <button
          @click="runAnalysis"
          :disabled="isAnalyzing || !hasObjectives || llmStatus?.configured === false"
          class="btn-primary"
        >
          <svg v-if="isAnalyzing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span>{{ isAnalyzing ? 'Analyzing...' : 'Run Objective Analysis (AI)' }}</span>
        </button>
      </div>

      <!-- Error message -->
      <div v-if="errorMessage" class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="mb-6 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm">
        {{ successMessage }}
      </div>

      <!-- Analysis results -->
      <div v-if="analysisResult" class="space-y-6 animate-slide-up">
        <!-- Overall assessment -->
        <div class="bg-brand-50 border border-brand-200 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <div class="font-medium text-brand-900 mb-1">Overall Assessment</div>
              <p class="text-sm text-brand-800">{{ stripMarkdown(analysisResult.overall_assessment || '') }}</p>
            </div>
          </div>
        </div>

        <!-- Bloom's Analysis -->
        <div v-if="analysisResult.bloom_analysis?.length">
          <div class="text-sm font-medium text-surface-700 mb-3">Bloom's Taxonomy Analysis</div>
          <div class="space-y-3">
            <div 
              v-for="(item, index) in analysisResult.bloom_analysis" 
              :key="index"
              class="p-4 bg-surface-50 rounded-lg"
            >
              <div class="flex items-start justify-between gap-4 mb-2">
                <p class="text-sm text-surface-900 font-medium">{{ item.objective }}</p>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <span class="badge badge-brand">{{ item.current_level }}</span>
                  <span 
                    class="badge"
                    :class="item.is_measurable ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
                  >
                    {{ item.is_measurable ? 'Measurable' : 'Not Measurable' }}
                  </span>
                </div>
              </div>
              <p class="text-sm text-surface-600">{{ stripMarkdown(item.suggestion || '') }}</p>
            </div>
          </div>
        </div>

        <!-- Improved objectives -->
        <div v-if="analysisResult.improved_objectives?.length">
          <div class="flex items-center justify-between gap-4 mb-3">
            <div class="text-sm font-medium text-surface-700">Suggested Improvements</div>
            <div class="flex items-center gap-2">
              <button class="btn-secondary" @click="copyImprovedObjectives">
                Copy
              </button>
              <button class="btn-secondary" @click="insertImprovedObjectives">
                Insert below
              </button>
              <button class="btn-primary" @click="replaceWithImprovedObjectives">
                Replace (clean)
              </button>
            </div>
          </div>
          <ul class="space-y-2">
            <li 
              v-for="(objective, index) in analysisResult.improved_objectives" 
              :key="index"
              class="flex items-start gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg"
            >
              <span class="w-6 h-6 rounded-full bg-emerald-200 text-emerald-700 flex items-center justify-center flex-shrink-0 text-xs font-medium">
                {{ index + 1 }}
              </span>
              <div class="flex-1 min-w-0">
                <span class="text-sm text-emerald-800">{{ objective }}</span>
              </div>
              <button
                class="btn-ghost text-sm px-3 py-1.5 flex-shrink-0"
                @click="copyText(objective, 'Copied this suggestion (cleaned markdown).')"
                title="Copy this suggestion"
              >
                Copy
              </button>
            </li>
          </ul>
        </div>

        <!-- Alignment notes -->
        <div v-if="analysisResult.alignment_notes" class="p-4 bg-surface-50 rounded-lg">
          <div class="text-sm font-medium text-surface-700 mb-2">Alignment Notes</div>
          <p class="text-sm text-surface-600">{{ stripMarkdown(analysisResult.alignment_notes || '') }}</p>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!errorMessage" class="text-center py-8 text-surface-500">
        <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p class="text-sm">Click "Run Objective Analysis" to get AI-powered feedback.</p>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex justify-between">
      <button
        @click="router.push('/new-session')"
        class="btn-secondary"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        Back to Context
      </button>
      <button
        @click="proceedToActivities"
        class="btn-primary"
      >
        Continue to Activities
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
    </div>
  </div>
</template>
