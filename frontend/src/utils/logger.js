/**
 * Solstice Events — Client-side Logger
 *
 * Levels: INFO | WARN | ERROR | API
 *
 * - Prints structured lines to the browser console with timestamps.
 * - Stores the last 200 entries in localStorage under "solstice_logs"
 *   so you can inspect them even after a page refresh.
 * - Call logger.download() from the browser console to download the
 *   full log as a .txt file for sharing / debugging.
 *
 * Usage:
 *   import logger from '@/utils/logger'
 *   logger.info('Dashboard mounted')
 *   logger.api('GET', '/events', 200, 142)
 *   logger.error('Check-in failed', err)
 */

const MAX_ENTRIES = 200
const STORAGE_KEY = 'solstice_logs'

function timestamp() {
  return new Date().toISOString()
}

function getStored() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function store(entry) {
  try {
    const entries = getStored()
    entries.push(entry)
    // Keep only the last MAX_ENTRIES
    if (entries.length > MAX_ENTRIES) entries.splice(0, entries.length - MAX_ENTRIES)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
  } catch {
    // localStorage full or unavailable — silent
  }
}

function write(level, message, extra) {
  const entry = {
    ts: timestamp(),
    level,
    message,
    ...(extra !== undefined ? { extra } : {}),
  }

  store(entry)

  const prefix = `[Solstice ${entry.ts}] [${level}]`
  switch (level) {
    case 'ERROR':
      console.error(prefix, message, extra ?? '')
      break
    case 'WARN':
      console.warn(prefix, message, extra ?? '')
      break
    case 'API':
      // Colour-code by status: green <400, amber 4xx, red 5xx/network
      if (typeof extra?.status === 'number') {
        const style = extra.status < 400
          ? 'color:#16a34a;font-weight:600'
          : extra.status < 500
            ? 'color:#d97706;font-weight:600'
            : 'color:#dc2626;font-weight:600'
        console.log(`%c${prefix} ${message}`, style, extra)
      } else {
        console.log(prefix, message, extra ?? '')
      }
      break
    default:
      console.log(prefix, message, extra ?? '')
  }
}

const logger = {
  /** General informational event */
  info(message, extra) {
    write('INFO', message, extra)
  },

  /** Non-fatal warning */
  warn(message, extra) {
    write('WARN', message, extra)
  },

  /** Error — caught exception or unexpected state */
  error(message, errorOrExtra) {
    const extra =
      errorOrExtra instanceof Error
        ? { message: errorOrExtra.message, stack: errorOrExtra.stack }
        : errorOrExtra
    write('ERROR', message, extra)
  },

  /**
   * API call completed.
   * @param {string} method   - HTTP verb
   * @param {string} url      - endpoint path
   * @param {number} status   - HTTP status code (0 = network error)
   * @param {number} ms       - round-trip time in milliseconds
   */
  api(method, url, status, ms) {
    const emoji = status === 0 ? '🔴' : status < 400 ? '🟢' : status < 500 ? '🟡' : '🔴'
    write('API', `${emoji} ${method} ${url} → ${status || 'ERR'} (${ms}ms)`, { method, url, status, ms })
  },

  /** Return all stored log entries */
  getHistory() {
    return getStored()
  },

  /** Clear the stored log history */
  clear() {
    localStorage.removeItem(STORAGE_KEY)
    console.log('[Solstice Logger] Log history cleared.')
  },

  /**
   * Download the full log history as a .txt file.
   * Call from browser DevTools console: logger.download()
   */
  download() {
    const entries = getStored()
    const text = entries
      .map(e => `[${e.ts}] [${e.level}] ${e.message}${e.extra ? ' ' + JSON.stringify(e.extra) : ''}`)
      .join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `solstice-logs-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(a.href)
  },
}

// Expose on window so DevTools console can call: logger.download(), logger.getHistory()
if (typeof window !== 'undefined') {
  window.__solsticeLogger = logger
}

export default logger
