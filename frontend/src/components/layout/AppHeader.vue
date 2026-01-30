<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const sessionStore = useSessionStore()

function goHome() {
  router.push('/')
}

function startNewSession() {
  sessionStore.resetSession()
  router.push('/new-session')
}
</script>

<template>
  <header class="bg-white border-b border-surface-200 sticky top-0 z-50">
    <div class="px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <button 
          @click="goHome"
          class="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h12M4 18h8" />
            </svg>
          </div>
          <div>
            <span class="font-semibold text-surface-900">ID-DSS</span>
            <span class="hidden sm:inline text-surface-500 text-sm ml-2">Instructional Design Support</span>
          </div>
        </button>

        <!-- Actions -->
        <div class="flex items-center gap-4">
          <button
            v-if="sessionStore.hasActiveSession"
            @click="startNewSession"
            class="btn-ghost text-sm"
          >
            New Session
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

