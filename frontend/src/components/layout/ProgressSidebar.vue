<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()

interface Step {
  id: string
  name: string
  route: string
  icon: string
}

const steps: Step[] = [
  { id: 'context', name: 'Course Context', route: '/new-session', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { id: 'objectives', name: 'Objective Analysis', route: '/objective-analysis', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
  { id: 'activities', name: 'Activity Suggestions', route: '/activity-suggestion', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
  { id: 'summary', name: 'Summary & Export', route: '/summary', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
]

const currentStepIndex = computed(() => {
  return steps.findIndex(step => step.route === route.path)
})

function isStepComplete(index: number): boolean {
  return index < currentStepIndex.value
}

function isStepActive(index: number): boolean {
  return index === currentStepIndex.value
}

function isStepAccessible(index: number): boolean {
  // Can access current or previous steps
  return index <= currentStepIndex.value || sessionStore.hasActiveSession
}

function navigateToStep(step: Step, index: number) {
  if (isStepAccessible(index)) {
    router.push(step.route)
  }
}
</script>

<template>
  <aside class="hidden lg:block fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-surface-200 p-6">
    <div class="mb-6">
      <h2 class="text-xs font-semibold text-surface-500 uppercase tracking-wider">Design Progress</h2>
    </div>

    <nav class="space-y-1">
      <button
        v-for="(step, index) in steps"
        :key="step.id"
        @click="navigateToStep(step, index)"
        :disabled="!isStepAccessible(index)"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200"
        :class="{
          'bg-brand-50 text-brand-700': isStepActive(index),
          'text-surface-600 hover:bg-surface-50': !isStepActive(index) && isStepAccessible(index),
          'text-surface-400 cursor-not-allowed': !isStepAccessible(index),
        }"
      >
        <!-- Step indicator -->
        <div 
          class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
          :class="{
            'bg-brand-600 text-white': isStepComplete(index),
            'bg-brand-100 text-brand-600': isStepActive(index),
            'bg-surface-100 text-surface-400': !isStepComplete(index) && !isStepActive(index),
          }"
        >
          <!-- Checkmark for completed -->
          <svg v-if="isStepComplete(index)" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <!-- Step number for incomplete -->
          <span v-else class="text-sm font-medium">{{ index + 1 }}</span>
        </div>

        <!-- Step name -->
        <span class="text-sm font-medium">{{ step.name }}</span>
      </button>
    </nav>

    <!-- Session info -->
    <div v-if="sessionStore.hasActiveSession" class="mt-8 pt-6 border-t border-surface-200">
      <div class="text-xs font-medium text-surface-500 mb-2">Current Session</div>
      <div class="text-sm text-surface-900 font-medium truncate">
        {{ sessionStore.courseContext.course_title || 'Untitled' }}
      </div>
      <div class="text-xs text-surface-500 mt-1">
        Session #{{ sessionStore.sessionId }}
      </div>
    </div>
  </aside>
</template>

