<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { suggestActivities, createAction, getLLMStatus } from '@/services/api'
import type { ActivityItem, LLMStatus, ActionType } from '@/types'
import { stripMarkdown } from '@/utils/text'

const router = useRouter()
const sessionStore = useSessionStore()

const isGenerating = ref(false)
const llmStatus = ref<LLMStatus | null>(null)
const stepId = ref<number | null>(null)
const recommendationId = ref<number | null>(null)
const errorMessage = ref('')

interface ActivityWithStatus extends ActivityItem {
  id: string
  status: 'pending' | 'accepted' | 'rejected' | 'editing'
  draft?: {
    title: string
    type: string
    description: string
    duration: string
    materials_needed: string
  }
}

const activities = ref<ActivityWithStatus[]>([])
const sequenceRationale = ref<string>('')
const totalEstimatedTime = ref<string>('')

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

  // Hydrate from store if we already have suggestions (e.g. user navigated back)
  if (sessionStore.activitySuggestions?.length) {
    activities.value = sessionStore.activitySuggestions.map((activity, index) => ({
      id: `activity-${index}`,
      ...activity,
      status: 'pending' as const,
    }))
  }
})

async function generateSuggestions() {
  if (!sessionStore.sessionId) return
  
  isGenerating.value = true
  errorMessage.value = ''
  
  try {
    // Reset last run so UI doesn't look "stuck" if response is empty
    activities.value = []
    sequenceRationale.value = ''
    totalEstimatedTime.value = ''

    const result = await suggestActivities(
      sessionStore.sessionId,
      sessionStore.courseContext.learning_objectives
    )
    
    stepId.value = result.step_id
    recommendationId.value = result.recommendation_id
    
    const data = result.data as {
      activities?: ActivityItem[]
      sequence_rationale?: string
      total_estimated_time?: string
      raw_response?: string
      parse_error?: boolean
    }

    sequenceRationale.value = stripMarkdown(data.sequence_rationale || '')
    totalEstimatedTime.value = stripMarkdown(data.total_estimated_time || '')
    
    const list = data.activities || []
    const cleanedList = list.map((activity) => ({
      ...activity,
      title: stripMarkdown(activity.title || ''),
      type: stripMarkdown(activity.type || ''),
      description: stripMarkdown(activity.description || ''),
      duration: stripMarkdown(activity.duration || ''),
      assessment_criteria: stripMarkdown(activity.assessment_criteria || ''),
      objective_alignment: (activity.objective_alignment || []).map((x) => stripMarkdown(x || '')).filter(Boolean),
      materials_needed: (activity.materials_needed || []).map((x) => stripMarkdown(x || '')).filter(Boolean),
      instructions: (activity.instructions || []).map((x) => stripMarkdown(x || '')).filter(Boolean),
      adaptations: {
        online: stripMarkdown(activity.adaptations?.online || ''),
        accessibility: stripMarkdown(activity.adaptations?.accessibility || ''),
      },
    }))

    activities.value = cleanedList.map((activity, index) => ({
      id: `activity-${index}`,
      ...activity,
      status: 'pending' as const,
    }))

    // Persist for navigation/summary pages
    sessionStore.setActivitySuggestions(cleanedList)
    
    // Store in session
    sessionStore.addDesignStep({
      id: result.step_id,
      session_id: sessionStore.sessionId,
      phase: 'activity-suggestion',
      user_input: sessionStore.courseContext.learning_objectives,
      created_at: new Date().toISOString(),
    })

    // If backend returned an unexpected shape, make it visible instead of silent no-op.
    if (activities.value.length === 0) {
      if (data.parse_error && data.raw_response) {
        errorMessage.value = 'The AI response could not be parsed as valid JSON. Try again, or adjust the prompt/model.'
      } else {
        errorMessage.value = 'No activities were returned. Try generating again, or refine your objectives.'
      }
    }
    
  } catch (error: unknown) {
    console.error('Generation failed:', error)
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      errorMessage.value = axiosError.response?.data?.detail || 'Generation failed. Please try again.'
    } else {
      errorMessage.value = 'Generation failed. Please try again.'
    }
  } finally {
    isGenerating.value = false
  }
}

async function saveAction(activityId: string, actionType: ActionType, editedContent?: string, comment?: string) {
  if (!stepId.value) return
  
  try {
    await createAction({
      step_id: stepId.value,
      recommendation_id: recommendationId.value || undefined,
      action_type: actionType,
      edited_content: editedContent,
      comment: comment || activityId, // Store activity ID as reference
    })
  } catch (error) {
    console.error('Failed to save action:', error)
  }
}

async function acceptActivity(id: string) {
  const activity = activities.value.find(a => a.id === id)
  if (activity) {
    activity.status = 'accepted'
    await saveAction(id, 'accept', JSON.stringify(activity))
  }
}

async function rejectActivity(id: string) {
  const activity = activities.value.find(a => a.id === id)
  if (activity) {
    activity.status = 'rejected'
    await saveAction(id, 'reject')
  }
}

function editActivity(id: string) {
  const activity = activities.value.find(a => a.id === id)
  if (activity) {
    activity.status = 'editing'
    activity.draft = {
      title: activity.title || '',
      type: activity.type || '',
      description: activity.description || '',
      duration: activity.duration || '',
      materials_needed: (activity.materials_needed || []).join(', '),
    }
  }
}

async function saveEdits(id: string) {
  const activity = activities.value.find(a => a.id === id)
  if (!activity?.draft) return

  activity.title = activity.draft.title
  activity.type = activity.draft.type
  activity.description = activity.draft.description
  activity.duration = activity.draft.duration
  activity.materials_needed = activity.draft.materials_needed
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)

  activity.status = 'pending'
  delete activity.draft

  // Persist to store (drop UI-only fields)
  sessionStore.setActivitySuggestions(
    activities.value.map(({ id: _id, status: _status, draft: _draft, ...rest }) => rest)
  )

  await saveAction(id, 'edit', JSON.stringify(activity), 'Edited activity content')
}

function cancelEdits(id: string) {
  const activity = activities.value.find(a => a.id === id)
  if (!activity) return
  activity.status = 'pending'
  delete activity.draft
}

async function regenerateActivity(id: string) {
  await saveAction(id, 'regenerate')
  // TODO: Implement single activity regeneration
  alert('Regeneration for single activity coming soon! Click "Generate Activity Suggestions" to get new suggestions.')
}

function proceedToSummary() {
  sessionStore.setCurrentPhase('summary')
  router.push('/summary')
}

function getStatusBadgeClass(status: string) {
  switch (status) {
    case 'accepted': return 'bg-emerald-100 text-emerald-700'
    case 'rejected': return 'bg-red-100 text-red-700'
    case 'editing': return 'bg-amber-100 text-amber-700'
    default: return 'bg-surface-100 text-surface-600'
  }
}

function getTypeIcon(type: string) {
  const typeLower = type?.toLowerCase() || ''
  switch (typeLower) {
    case 'discussion':
      return 'M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z'
    case 'project':
    case 'lab':
      return 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'
    case 'assessment':
    case 'reflection':
      return 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
    case 'presentation':
      return 'M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z'
    case 'case study':
    case 'simulation':
      return 'M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2'
    default:
      return 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'
  }
}

function getTypeColorClass(type: string) {
  const typeLower = type?.toLowerCase() || ''
  switch (typeLower) {
    case 'discussion': return 'bg-violet-100 text-violet-600'
    case 'project':
    case 'lab': return 'bg-amber-100 text-amber-600'
    case 'assessment':
    case 'reflection': return 'bg-brand-100 text-brand-600'
    case 'presentation': return 'bg-blue-100 text-blue-600'
    case 'case study':
    case 'simulation': return 'bg-rose-100 text-rose-600'
    default: return 'bg-surface-100 text-surface-600'
  }
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Page header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-surface-900 mb-2">Activity Suggestions</h1>
      <p class="text-surface-600">
        Generate AI-powered learning activity suggestions based on your objectives.
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

    <!-- Generate button section -->
    <div class="card p-6 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="font-semibold text-surface-900">Generate Activities</h2>
          <p class="text-sm text-surface-500 mt-1">Get contextual suggestions for learning activities aligned with your objectives.</p>
        </div>
        <button
          @click="generateSuggestions"
          :disabled="isGenerating || llmStatus?.configured === false"
          class="btn-primary"
        >
          <svg v-if="isGenerating" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span>{{ isGenerating ? 'Generating...' : 'Generate Activity Suggestions (AI)' }}</span>
        </button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
      {{ errorMessage }}
    </div>

    <!-- Activity cards -->
    <div v-if="sequenceRationale || totalEstimatedTime" class="card p-6 mb-6">
      <div v-if="sequenceRationale" class="mb-3">
        <div class="text-sm font-medium text-surface-700 mb-1">Sequence Rationale</div>
        <p class="text-sm text-surface-600">{{ sequenceRationale }}</p>
      </div>
      <div v-if="totalEstimatedTime">
        <div class="text-sm font-medium text-surface-700 mb-1">Total Estimated Time</div>
        <p class="text-sm text-surface-600">{{ totalEstimatedTime }}</p>
      </div>
    </div>

    <div v-if="activities.length > 0" class="space-y-4 mb-6">
      <div
        v-for="(activity, index) in activities"
        :key="activity.id"
        class="card p-6 animate-slide-up"
        :style="{ animationDelay: `${index * 100}ms` }"
        :class="{
          'border-emerald-300 bg-emerald-50/50': activity.status === 'accepted',
          'border-red-300 bg-red-50/50 opacity-60': activity.status === 'rejected',
        }"
      >
        <div class="flex items-start gap-4">
          <!-- Activity type icon -->
          <div 
            class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
            :class="getTypeColorClass(activity.type)"
          >
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" :d="getTypeIcon(activity.type)" />
            </svg>
          </div>

          <!-- Activity content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 mb-2">
              <h3 v-if="activity.status !== 'editing'" class="font-semibold text-surface-900">{{ activity.title }}</h3>
              <input
                v-else
                v-model="activity.draft!.title"
                class="w-full max-w-xl bg-white border border-surface-200 rounded px-3 py-1.5 text-sm"
                placeholder="Activity title"
              />
              <span 
                class="badge text-xs capitalize flex-shrink-0"
                :class="getStatusBadgeClass(activity.status)"
              >
                {{ activity.status }}
              </span>
            </div>

            <div v-if="activity.status === 'editing'" class="space-y-3 mb-3">
              <div class="grid sm:grid-cols-2 gap-3">
                <div>
                  <div class="text-xs text-surface-500 mb-1">Type</div>
                  <input
                    v-model="activity.draft!.type"
                    class="w-full bg-white border border-surface-200 rounded px-3 py-1.5 text-sm"
                    placeholder="e.g. Discussion / Case Study / Project"
                  />
                </div>
                <div>
                  <div class="text-xs text-surface-500 mb-1">Duration</div>
                  <input
                    v-model="activity.draft!.duration"
                    class="w-full bg-white border border-surface-200 rounded px-3 py-1.5 text-sm"
                    placeholder="e.g. 45 minutes"
                  />
                </div>
              </div>

              <div>
                <div class="text-xs text-surface-500 mb-1">Description</div>
                <textarea
                  v-model="activity.draft!.description"
                  rows="4"
                  class="w-full bg-white border border-surface-200 rounded px-3 py-2 text-sm"
                  placeholder="Activity description"
                />
              </div>

              <div>
                <div class="text-xs text-surface-500 mb-1">Materials (comma-separated)</div>
                <input
                  v-model="activity.draft!.materials_needed"
                  class="w-full bg-white border border-surface-200 rounded px-3 py-1.5 text-sm"
                  placeholder="e.g. laptop, worksheet, slides"
                />
              </div>
            </div>

            <template v-else>
              <p class="text-sm text-surface-600 mb-3">{{ activity.description }}</p>
              
              <div class="flex items-center gap-4 text-xs text-surface-500 mb-3">
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ activity.duration }}
                </span>
                <span class="badge badge-neutral">{{ activity.type }}</span>
              </div>
            </template>

            <!-- Objective alignment -->
            <div v-if="activity.objective_alignment?.length" class="mb-3">
              <div class="text-xs text-surface-500 mb-1">Aligns with:</div>
              <div class="flex flex-wrap gap-1">
                <span 
                  v-for="(obj, i) in activity.objective_alignment" 
                  :key="i"
                  class="text-xs px-2 py-0.5 bg-brand-50 text-brand-700 rounded"
                >
                  {{ obj }}
                </span>
              </div>
            </div>

            <!-- Materials needed -->
            <div v-if="activity.materials_needed?.length" class="text-xs text-surface-500">
              <span class="font-medium">Materials:</span> {{ activity.materials_needed.join(', ') }}
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-2 flex-shrink-0">
            <template v-if="activity.status === 'editing'">
              <button
                @click="saveEdits(activity.id)"
                class="btn-success text-sm px-3 py-1.5"
              >
                Save
              </button>
              <button
                @click="cancelEdits(activity.id)"
                class="btn-secondary text-sm px-3 py-1.5"
              >
                Cancel
              </button>
            </template>
            <template v-else>
            <button
              @click="acceptActivity(activity.id)"
              :disabled="activity.status === 'accepted'"
              class="btn-success text-sm px-3 py-1.5"
              :class="{ 'opacity-50 cursor-not-allowed': activity.status === 'accepted' }"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Accept
            </button>
            <button
              @click="editActivity(activity.id)"
              class="btn-secondary text-sm px-3 py-1.5"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </button>
            <button
              @click="rejectActivity(activity.id)"
              :disabled="activity.status === 'rejected'"
              class="btn-danger text-sm px-3 py-1.5"
              :class="{ 'opacity-50 cursor-not-allowed': activity.status === 'rejected' }"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Reject
            </button>
            <button
              @click="regenerateActivity(activity.id)"
              class="btn-ghost text-sm px-3 py-1.5"
              title="Regenerate this suggestion"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!errorMessage" class="card p-12 text-center mb-6">
      <svg class="w-16 h-16 mx-auto mb-4 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
      <h3 class="text-lg font-medium text-surface-900 mb-2">No Activities Generated Yet</h3>
      <p class="text-surface-500 max-w-md mx-auto">
        Click the "Generate Activity Suggestions" button above to get AI-powered recommendations based on your learning objectives.
      </p>
    </div>

    <!-- Navigation -->
    <div class="flex justify-between">
      <button
        @click="router.push('/objective-analysis')"
        class="btn-secondary"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        Back to Analysis
      </button>
      <button
        @click="proceedToSummary"
        class="btn-primary"
      >
        Continue to Summary
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
    </div>
  </div>
</template>
