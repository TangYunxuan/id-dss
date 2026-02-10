<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { downloadSessionExportDocx, downloadSessionExportPdf } from '@/services/api'

const router = useRouter()
const sessionStore = useSessionStore()

const isExporting = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  // Redirect if no session
  if (!sessionStore.hasActiveSession) {
    router.push('/new-session')
    return
  }
})

const sessionSummary = computed(() => ({
  course: sessionStore.courseContext.course_title,
  level: sessionStore.courseContext.level,
  modality: sessionStore.courseContext.modality,
  constraints: sessionStore.courseContext.constraints,
  objectives: sessionStore.courseContext.learning_objectives,
  sessionId: sessionStore.sessionId,
  createdAt: sessionStore.currentSession?.created_at,
}))

async function handleExport() {
  if (!sessionStore.sessionId) return
  
  isExporting.value = true
  errorMessage.value = ''
  
  try {
    await downloadSessionExportDocx(sessionStore.sessionId)
  } catch (error) {
    console.error('Export failed:', error)
    errorMessage.value = 'Export failed. Please try again.'
  } finally {
    isExporting.value = false
  }
}

async function handleExportPdf() {
  if (!sessionStore.sessionId) return
  
  isExporting.value = true
  errorMessage.value = ''
  
  try {
    await downloadSessionExportPdf(sessionStore.sessionId)
  } catch (error) {
    console.error('Export failed:', error)
    errorMessage.value = 'Export failed. Please try again.'
  } finally {
    isExporting.value = false
  }
}

function startNewSession() {
  sessionStore.resetSession()
  router.push('/new-session')
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Page header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-surface-900">Session Summary</h1>
      </div>
      <p class="text-surface-600">
        Review your design session and export the complete data.
      </p>
    </div>

    <!-- Summary cards -->
    <div class="space-y-6 mb-8">
      <!-- Course info card -->
      <div class="card p-6">
        <h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">Course Information</h2>
        
        <div class="grid sm:grid-cols-2 gap-6">
          <div>
            <div class="text-xs text-surface-500 mb-1">Course Title</div>
            <div class="font-medium text-surface-900">{{ sessionSummary.course || 'Not specified' }}</div>
          </div>
          <div>
            <div class="text-xs text-surface-500 mb-1">Session ID</div>
            <div class="font-mono text-sm text-surface-700">#{{ sessionSummary.sessionId }}</div>
          </div>
          <div>
            <div class="text-xs text-surface-500 mb-1">Education Level</div>
            <div class="font-medium text-surface-900 capitalize">{{ sessionSummary.level?.replace('-', ' ') || 'Not specified' }}</div>
          </div>
          <div>
            <div class="text-xs text-surface-500 mb-1">Delivery Modality</div>
            <div class="font-medium text-surface-900 capitalize">{{ sessionSummary.modality?.replace('-', ' ') || 'Not specified' }}</div>
          </div>
        </div>
      </div>

      <!-- Objectives card -->
      <div class="card p-6">
        <h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">Learning Objectives</h2>
        
        <div v-if="sessionSummary.objectives" class="bg-surface-50 rounded-lg p-4 text-sm text-surface-700 whitespace-pre-wrap">
          {{ sessionSummary.objectives }}
        </div>
        <div v-else class="bg-surface-50 rounded-lg p-4 text-sm text-surface-500 italic">
          No learning objectives were specified for this session.
        </div>
      </div>

      <!-- Constraints card -->
      <div v-if="sessionSummary.constraints" class="card p-6">
        <h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">Constraints & Requirements</h2>
        
        <div class="bg-surface-50 rounded-lg p-4 text-sm text-surface-700 whitespace-pre-wrap">
          {{ sessionSummary.constraints }}
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
      {{ errorMessage }}
    </div>

    <!-- Export section -->
    <div class="card p-6 bg-gradient-to-br from-brand-50 to-brand-100/50 border-brand-200 mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="font-semibold text-brand-900 mb-1">Export Session Data</h2>
          <p class="text-sm text-brand-700">
            Download your complete design session including all steps, AI recommendations, and your decisions.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleExport"
            :disabled="isExporting"
            class="btn-primary"
          >
            <svg v-if="isExporting" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>{{ isExporting ? 'Exporting...' : 'Export Word' }}</span>
          </button>
          <button
            @click="handleExportPdf"
            :disabled="isExporting"
            class="btn-secondary"
          >
            Export PDF
          </button>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex justify-between">
      <button
        @click="router.push('/activity-suggestion')"
        class="btn-secondary"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        Back to Activities
      </button>
      <button
        @click="startNewSession"
        class="btn-primary"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Start New Session
      </button>
    </div>
  </div>
</template>
