<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
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

onMounted(() => {
  // If user navigates back with an active session, prefill the form from the store
  if (hasExistingSession.value) {
    Object.assign(form, sessionStore.courseContext)
  }
})

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
          <textarea
            id="learning_objectives"
            v-model="form.learning_objectives"
            class="textarea-field"
            rows="5"
            placeholder="Enter your learning objectives, one per line...&#10;&#10;e.g.,&#10;• Students will be able to explain the fundamentals of supervised learning&#10;• Students will be able to implement a basic neural network"
          />
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

