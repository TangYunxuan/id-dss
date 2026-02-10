<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { createSession, updateSession } from '@/services/api'
import type { CourseContextForm } from '@/types'

const router = useRouter()
const sessionStore = useSessionStore()

const isSubmitting = ref(false)
const errorMessage = ref('')
const hasExistingSession = computed(() => sessionStore.hasActiveSession && !!sessionStore.sessionId)

const form = reactive<CourseContextForm>({
  course_title: '',
  level: '',
  modality: '',
  constraints: '',
  learning_objectives: '',
})

function normalizeObjectiveLine(line: string): string {
  return (line || '')
    .replace(/^\s*(?:[-*•]|\d+\.)\s+/, '')
    .trim()
}

function parseObjectivesText(text: string): string[] {
  const raw = (text || '').replace(/\r\n/g, '\n').trim()
  if (!raw) return []
  return raw
    .split('\n')
    .map(normalizeObjectiveLine)
    .filter(Boolean)
}

function joinObjectives(lines: string[]): string {
  return (lines || []).map(normalizeObjectiveLine).filter(Boolean).join('\n')
}

const objectivesLines = ref<string[]>([])
const showBulkPaste = ref(false)
const bulkObjectivesText = ref('')

onMounted(() => {
  // If user navigates back with an active session, prefill the form from the store
  if (hasExistingSession.value) {
    Object.assign(form, sessionStore.courseContext)
  }
  objectivesLines.value = parseObjectivesText(form.learning_objectives || '')
})

watch(
  objectivesLines,
  (lines) => {
    form.learning_objectives = joinObjectives(lines)
  },
  { deep: true }
)

function addObjectiveLine() {
  objectivesLines.value.push('')
}

function removeObjectiveLine(idx: number) {
  objectivesLines.value.splice(idx, 1)
}

function applyBulkPaste() {
  const lines = parseObjectivesText(bulkObjectivesText.value)
  if (lines.length === 0) return
  objectivesLines.value = [...objectivesLines.value, ...lines]
  bulkObjectivesText.value = ''
  showBulkPaste.value = false
}

const levelOptions = [
  { value: 'undergraduate', label: 'Undergraduate' },
  { value: 'graduate', label: 'Graduate' },
]

const modalityOptions = [
  { value: 'in-person', label: 'In-Person' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'online', label: 'Online' },
]

async function handleSubmit() {
  if (!form.course_title || !form.level || !form.modality) {
    errorMessage.value = 'Please fill in all required fields.'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    let session = sessionStore.currentSession

    if (hasExistingSession.value && sessionStore.sessionId) {
      // Update existing session in backend
      session = await updateSession(sessionStore.sessionId, {
        course_title: form.course_title,
        level: form.level,
        modality: form.modality,
        constraints: form.constraints || undefined,
        learning_objectives: form.learning_objectives || undefined,
      })
    } else {
      // Create session in backend
      session = await createSession({
        course_title: form.course_title,
        level: form.level,
        modality: form.modality,
        constraints: form.constraints || undefined,
        learning_objectives: form.learning_objectives || undefined,
      })
    }

    // Store session data
    sessionStore.setSession(session)
    sessionStore.setCourseContext(form)
    sessionStore.setCurrentPhase('objective-analysis')

    // Navigate to next step
    router.push('/objective-analysis')
  } catch (error) {
    console.error('Failed to create session:', error)
    errorMessage.value = 'Failed to create session. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Page header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-surface-900 mb-2">Course Context</h1>
      <p class="text-surface-600">
        Provide information about your course to help the AI generate relevant suggestions.
      </p>
    </div>

    <!-- Form -->
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <div class="card p-6 space-y-6">
        <!-- Course Title -->
        <div>
          <label for="course_title" class="input-label">
            Course Title <span class="text-red-500">*</span>
          </label>
          <input
            id="course_title"
            v-model="form.course_title"
            type="text"
            class="input-field"
            placeholder="e.g., Introduction to Machine Learning"
            required
          />
        </div>

        <!-- Level & Modality Row -->
        <div class="grid sm:grid-cols-2 gap-6">
          <!-- Level -->
          <div>
            <label for="level" class="input-label">
              Education Level <span class="text-red-500">*</span>
            </label>
            <select
              id="level"
              v-model="form.level"
              class="select-field"
              required
            >
              <option value="" disabled>Select level...</option>
              <option 
                v-for="option in levelOptions" 
                :key="option.value" 
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>

          <!-- Modality -->
          <div>
            <label for="modality" class="input-label">
              Delivery Modality <span class="text-red-500">*</span>
            </label>
            <select
              id="modality"
              v-model="form.modality"
              class="select-field"
              required
            >
              <option value="" disabled>Select modality...</option>
              <option 
                v-for="option in modalityOptions" 
                :key="option.value" 
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <!-- Learning Objectives -->
        <div>
          <label for="learning_objectives" class="input-label">
            Learning Objectives
          </label>
          <div class="space-y-3">
            <div v-if="objectivesLines.length === 0" class="bg-surface-50 rounded-lg p-4 text-sm text-surface-500 italic">
              No objectives yet. Add one below, or paste multiple at once.
            </div>

            <div v-for="(_, idx) in objectivesLines" :key="idx" class="flex items-start gap-2">
              <div class="mt-2 w-6 text-xs text-surface-500 text-right flex-shrink-0">{{ idx + 1 }}.</div>
              <input
                :id="idx === 0 ? 'learning_objectives' : undefined"
                v-model="objectivesLines[idx]"
                type="text"
                class="input-field"
                placeholder="e.g., Students will be able to explain..."
              />
              <button
                type="button"
                class="btn-ghost text-sm px-3 py-2 flex-shrink-0"
                @click="removeObjectiveLine(idx)"
                title="Remove"
              >
                Remove
              </button>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <button type="button" class="btn-secondary" @click="addObjectiveLine">
                + Add objective
              </button>
              <button type="button" class="btn-ghost" @click="showBulkPaste = !showBulkPaste">
                {{ showBulkPaste ? 'Hide paste box' : 'Paste multiple' }}
              </button>
            </div>

            <div v-if="showBulkPaste" class="bg-surface-50 border border-surface-200 rounded-lg p-4">
              <div class="text-xs text-surface-500 mb-2">Paste objectives (one per line)</div>
              <textarea
                v-model="bulkObjectivesText"
                class="w-full bg-white rounded-lg p-3 text-sm text-surface-700 border border-surface-200 focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-300"
                rows="4"
                placeholder="• Objective 1&#10;• Objective 2&#10;• Objective 3"
              />
              <div class="flex justify-end mt-3">
                <button type="button" class="btn-primary" @click="applyBulkPaste">
                  Add to list
                </button>
              </div>
            </div>
          </div>
          <p class="mt-1.5 text-sm text-surface-500">
            These will be analyzed by the AI in the next step.
          </p>
        </div>

        <!-- Constraints -->
        <div>
          <label for="constraints" class="input-label">
            Constraints & Requirements
          </label>
          <textarea
            id="constraints"
            v-model="form.constraints"
            class="textarea-field"
            rows="3"
            placeholder="e.g., 15-week semester, max 30 students, limited lab access..."
          />
          <p class="mt-1.5 text-sm text-surface-500">
            Any limitations or specific requirements for the course design.
          </p>
        </div>
      </div>

      <!-- Error message -->
      <div v-if="errorMessage" class="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
        {{ errorMessage }}
      </div>

      <!-- Submit button -->
      <div class="flex justify-end">
        <button
          type="submit"
          class="btn-primary"
          :disabled="isSubmitting"
        >
          <svg v-if="isSubmitting" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span v-else>{{ hasExistingSession ? 'Save & Continue to Objective Analysis' : 'Continue to Objective Analysis' }}</span>
          <svg v-if="!isSubmitting" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </div>
    </form>
  </div>
</template>

