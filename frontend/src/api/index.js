import axios from 'axios'
import logger from '../utils/logger'

const BASE_URL = import.meta.env.VITE_API_URL

const api = axios.create({ baseURL: BASE_URL })

// ── Wake-up ping ──────────────────────────────────────────────────────────────
// Render free tier spins down after 15 min of inactivity. The first request
// after sleep takes ~30 s. We fire a silent GET / ping immediately when the
// JS bundle loads so the backend wakes up while the user is still looking at
// the page — by the time they click anything, the server is already warm.
let _woken = false
export function resetWakeGuard() { _woken = false }
export function pingBackend() {
  if (_woken) return
  _woken = true
  const t0 = Date.now()
  logger.info('Backend wake-up ping sent', { url: `${BASE_URL}/` })
  axios
    .get(`${BASE_URL}/`, { timeout: 35_000 })
    .then(() => {
      const ms = Date.now() - t0
      logger.info(`Backend awake ✓ (${ms}ms)`, { ms })
    })
    .catch((err) => {
      const ms = Date.now() - t0
      logger.warn('Backend wake-up ping failed — server may still be starting', {
        ms,
        error: err.message,
      })
    })
}

// ── Request interceptor — attach token + log outgoing request ─────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`

  // Stamp the start time so the response interceptor can compute round-trip ms
  config.metadata = { startTime: Date.now() }

  logger.info(`→ ${config.method?.toUpperCase()} ${config.url}`, {
    params: config.params,
    hasBody: Boolean(config.data),
  })

  return config
})

// ── Response interceptor — log success + errors ───────────────────────────────
api.interceptors.response.use(
  (response) => {
    const ms = Date.now() - (response.config.metadata?.startTime ?? Date.now())
    logger.api(
      response.config.method?.toUpperCase(),
      response.config.url,
      response.status,
      ms,
    )
    return response
  },
  (error) => {
    const ms = Date.now() - (error.config?.metadata?.startTime ?? Date.now())
    const status = error.response?.status ?? 0
    const detail = error.response?.data?.detail ?? error.message

    logger.api(
      error.config?.method?.toUpperCase() ?? '?',
      error.config?.url ?? '?',
      status,
      ms,
    )

    // Log the full error detail separately so it's easy to find
    logger.error(`API error ${status} on ${error.config?.url}`, {
      status,
      detail,
      method: error.config?.method?.toUpperCase(),
    })

    // 401 — token expired / invalid → clear auth and redirect to login
    if (status === 401) {
      logger.warn('401 received — clearing auth token and redirecting to /login')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default api
