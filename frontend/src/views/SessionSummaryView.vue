<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { downloadSessionExportDocx, downloadSessionExportPdf, exportSession } from '@/services/api'
import type { ExportData } from '@/services/api'

const router = useRouter()
const sessionStore = useSessionStore()

const isExporting = ref(false)
const isLoadingData = ref(false)
const exportData = ref<ExportData | null>(null)
const errorMessage = ref('')

onMounted(async () => {
  // Redirect if no session
  if (!sessionStore.hasActiveSession) {
    router.push('/new-session')
    return
  }
  
  // Load full export data for summary display
  await loadExportData()
})

async function loadExportData() {
  if (!sessionStore.sessionId) return
  
  isLoadingData.value = true
  try {
    exportData.value = await exportSession(sessionStore.sessionId)
  } catch (error) {
    console.error('Failed to load session data:', error)
  } finally {
    isLoadingData.value = false
  }
}

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

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
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

      <!-- Design activity summary -->
      <div class="card p-6">
        <h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">Design Activity Summary</h2>
        
        <div v-if="isLoadingData" class="flex items-center justify-center py-8">
          <svg class="w-6 h-6 animate-spin text-brand-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        
        <div v-else-if="exportData" class="space-y-4">
          <!-- Stats grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="bg-surface-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-surface-900">{{ exportData.summary.total_steps }}</div>
              <div class="text-xs text-surface-500">Design Steps</div>
            </div>
            <div class="bg-surface-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-brand-600">{{ exportData.summary.total_recommendations }}</div>
              <div class="text-xs text-surface-500">AI Recommendations</div>
            </div>
            <div class="bg-surface-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-emerald-600">{{ exportData.summary.total_actions }}</div>
              <div class="text-xs text-surface-500">User Actions</div>
            </div>
            <div class="bg-surface-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-surface-900">
                {{ Object.keys(exportData.summary.actions_by_type).length }}
              </div>
              <div class="text-xs text-surface-500">Action Types</div>
            </div>
          </div>

          <!-- Action breakdown -->
          <div v-if="Object.keys(exportData.summary.actions_by_type).length > 0">
            <div class="text-sm font-medium text-surface-700 mb-2">Actions by Type</div>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="(count, type) in exportData.summary.actions_by_type" 
                :key="type"
                class="px-3 py-1 rounded-full text-sm"
                :class="{
                  'bg-emerald-100 text-emerald-700': type === 'accept',
                  'bg-red-100 text-red-700': type === 'reject',
                  'bg-amber-100 text-amber-700': type === 'edit',
                  'bg-blue-100 text-blue-700': type === 'regenerate',
                  'bg-surface-100 text-surface-700': !['accept', 'reject', 'edit', 'regenerate'].includes(type as string),
                }"
              >
                {{ type }}: {{ count }}
              </span>
            </div>
          </div>

          <!-- Design steps timeline -->
          <div v-if="exportData.design_steps.length > 0">
            <div class="text-sm font-medium text-surface-700 mb-3">Design Steps</div>
            <div class="space-y-3">
              <div 
                v-for="step in exportData.design_steps" 
                :key="step.id"
                class="flex items-start gap-3 p-3 bg-surface-50 rounded-lg"
              >
                <div class="w-8 h-8 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-surface-900 capitalize">{{ step.phase.replace('-', ' ') }}</span>
                    <span class="badge badge-brand text-xs">{{ step.recommendations.length }} recommendations</span>
                    <span class="badge badge-neutral text-xs">{{ step.user_actions.length }} actions</span>
                  </div>
                  <div class="text-xs text-surface-500 mt-1">{{ formatDate(step.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="bg-surface-50 rounded-lg p-4 text-sm text-surface-500 italic text-center">
          No design activity recorded yet. Complete the design steps to see a summary here.
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
