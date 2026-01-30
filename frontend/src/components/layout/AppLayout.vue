<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './AppHeader.vue'
import ProgressSidebar from './ProgressSidebar.vue'

const route = useRoute()

const showSidebar = computed(() => {
  // Show sidebar on design flow pages
  const sidebarRoutes = ['new-session', 'objective-analysis', 'activity-suggestion', 'summary']
  return sidebarRoutes.includes(route.name as string)
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    
    <div class="flex-1 flex">
      <!-- Progress Sidebar -->
      <ProgressSidebar v-if="showSidebar" />
      
      <!-- Main Content -->
      <main 
        class="flex-1 p-6 lg:p-8"
        :class="{ 'lg:ml-64': showSidebar }"
      >
        <div class="max-w-4xl mx-auto">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

