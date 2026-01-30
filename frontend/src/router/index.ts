import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/new-session',
    name: 'new-session',
    component: () => import('@/views/CourseContextView.vue'),
  },
  {
    path: '/objective-analysis',
    name: 'objective-analysis',
    component: () => import('@/views/ObjectiveAnalysisView.vue'),
  },
  {
    path: '/activity-suggestion',
    name: 'activity-suggestion',
    component: () => import('@/views/ActivitySuggestionView.vue'),
  },
  {
    path: '/summary',
    name: 'summary',
    component: () => import('@/views/SessionSummaryView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router

