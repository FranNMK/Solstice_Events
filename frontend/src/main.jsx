import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import logger from './utils/logger.js'
import { pingBackend, resetWakeGuard } from './api/index.js'

// ── App boot log ──────────────────────────────────────────────────────────────
logger.info('Solstice Events app booting', {
  version: import.meta.env.VITE_APP_VERSION ?? 'dev',
  apiUrl: import.meta.env.VITE_API_URL,
  env: import.meta.env.MODE,
})

// ── Backend wake-up ping ──────────────────────────────────────────────────────
// Fire immediately so Render's free-tier backend is warm by the time the user
// interacts. The ping is a simple GET / that takes ≤35 s on a cold start.
pingBackend()

// ── Global uncaught error handler ────────────────────────────────────────────
// Catches synchronous errors that bubble out of any component without a
// React error boundary (e.g. errors in event handlers).
window.onerror = (message, source, lineno, colno, error) => {
  logger.error('Uncaught global error', {
    message,
    source,
    lineno,
    colno,
    stack: error?.stack,
  })
  // Return false so the browser still shows the error in DevTools
  return false
}

// ── Unhandled Promise rejection handler ──────────────────────────────────────
// Catches any Promise that rejects without a .catch() handler — e.g. a fire-
// and-forget async call that throws unexpectedly.
window.addEventListener('unhandledrejection', (event) => {
  logger.error('Unhandled promise rejection', {
    reason: event.reason instanceof Error
      ? { message: event.reason.message, stack: event.reason.stack }
      : String(event.reason),
  })
})

// ── Page visibility — re-ping when the user returns to the tab ───────────────
// If the user leaves for >15 min and comes back, the backend may have slept
// again. Re-ping whenever the tab becomes visible after being hidden.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    logger.info('Tab became visible — re-pinging backend')
    resetWakeGuard()
    pingBackend()
  }
})

// ── React mount ───────────────────────────────────────────────────────────────
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

logger.info('React tree mounted')
