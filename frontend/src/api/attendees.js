import api from './index'

export const registerForEvent    = (data)        => api.post('/attendees/register', data)
export const getMyRegistrations  = ()             => api.get('/attendees/my')
export const getAttendeeStatus   = (id)           => api.get(`/attendees/${id}/status`)
export const checkIn             = (qr_code_id)   => api.post('/checkin', { qr_code_id })
export const unregisterAttendee  = (id)           => api.delete(`/attendees/${id}`)

/**
 * Returns true if the given URL is a known Cloudflare R2 public URL.
 * Used to distinguish R2 URLs (always safe to open directly) from any
 * legacy Cloudinary URLs that might be stored in the DB (Cloudinary blocks
 * raw delivery with a 401/403, so they must NOT be opened directly).
 */
function _isR2Url(url) {
  if (!url) return false
  // Official R2 public bucket domains
  if (url.includes('.r2.dev')) return true
  if (url.includes('.r2.cloudflarestorage.com')) return true
  // Custom domain bound to R2 (not Cloudinary)
  if (url.includes('cloudflare') || url.includes('r2.')) return true
  // Local /static/... path — not a CDN URL at all
  if (url.startsWith('/')) return false
  // Any non-Cloudinary https URL is assumed to be a valid direct-serve CDN
  if (url.startsWith('https://') && !url.includes('res.cloudinary.com')) return true
  return false
}

/**
 * Resolve the badge URL for a checked-in attendee.
 *
 * Fast path (R2): badge_pdf_url is a public Cloudflare R2 URL stored on the
 * attendee record. Return it directly — the browser fetches the PDF straight
 * from R2 CDN with no backend hop, no auth header needed.
 *
 * Fallback (local dev / R2 not configured): badge_pdf_url is a /static/... path
 * OR is absent. Fetch via the authenticated axios instance, convert to a blob
 * URL, and return that so the download/print still works.
 * The caller must call URL.revokeObjectURL(url) when isBlob is true.
 *
 * Returns { url, isBlob }.
 */
export async function resolveBadgeUrl(attendeeId) {
  // Read badge_pdf_url from the status endpoint — already polled, so this is
  // usually a very fast round-trip.
  const { data } = await getAttendeeStatus(attendeeId)
  const pdfUrl = data.badge_pdf_url

  // R2 public URL — open directly from CDN, zero backend hop
  if (_isR2Url(pdfUrl)) {
    return { url: pdfUrl, isBlob: false }
  }

  // Local /static/... path or missing URL — stream through the backend endpoint
  const resp = await api.get(`/attendees/${attendeeId}/badge`, { responseType: 'blob' })
  const blob = new Blob([resp.data], { type: 'application/pdf' })
  return { url: URL.createObjectURL(blob), isBlob: true }
}
