import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'

// GitHub Pages SPA fallback: if we landed on "/?redirect=..."
// restore the intended path before mounting the router.
try {
  const params = new URLSearchParams(window.location.search)
  const redirect = params.get('redirect')
  if (redirect) {
    const restored = decodeURIComponent(redirect)
    // Remove the redirect param and restore the actual path for Vue Router.
    window.history.replaceState(null, '', restored)
  }
} catch {
  // no-op
}

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

