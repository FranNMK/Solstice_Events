import api from './index'

export const registerForEvent    = (data)        => api.post('/attendees/register', data)
export const getMyRegistrations  = ()             => api.get('/attendees/my')
export const getAttendeeStatus   = (id)           => api.get(`/attendees/${id}/status`)
export const checkIn             = (qr_code_id)   => api.post('/checkin', { qr_code_id })
export const unregisterAttendee  = (id)           => api.delete(`/attendees/${id}`)

/**
 * Resolve the badge URL for a checked-in attendee.
 *
 * Fast path (production): badge_pdf_url is a public R2 HTTPS URL stored on the
 * attendee record. Return it directly — the browser fetches the PDF straight
 * from R2 with no backend round-trip and no auth header needed.
 *
 * Fallback (local dev, R2 not configured): badge_pdf_url is a /static/... path.
 * Fetch via the authenticated axios instance, convert to a blob URL, and return
 * that so the download/print still works without CORS issues.
 * The caller must call URL.revokeObjectURL(url) when isBlob is true.
 *
 * Returns { url, isBlob }.
 */
export async function resolveBadgeUrl(attendeeId) {
  // Fetch the attendee status to read the stored badge_pdf_url directly.
  // This avoids an extra backend hop — the /badge endpoint just 302-redirects
  // to this same URL anyway.
  const { data } = await getAttendeeStatus(attendeeId)
  const pdfUrl = data.badge_pdf_url

  // Public R2 URL (or any absolute https:// URL) — serve directly from CDN
  if (pdfUrl && pdfUrl.startsWith('http')) {
    return { url: pdfUrl, isBlob: false }
  }

  // Local /static/... fallback: stream through the authenticated backend endpoint
  const resp = await api.get(`/attendees/${attendeeId}/badge`, { responseType: 'blob' })
  const blob = new Blob([resp.data], { type: 'application/pdf' })
  return { url: URL.createObjectURL(blob), isBlob: true }
}
