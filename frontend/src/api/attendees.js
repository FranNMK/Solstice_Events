import api from './index'

export const registerForEvent    = (data)        => api.post('/attendees/register', data)
export const getMyRegistrations  = ()             => api.get('/attendees/my')
export const getAttendeeStatus   = (id)           => api.get(`/attendees/${id}/status`)
export const checkIn             = (qr_code_id)   => api.post('/checkin', { qr_code_id })
export const unregisterAttendee  = (id)           => api.delete(`/attendees/${id}`)

/**
 * Resolve the badge URL for a checked-in attendee.
 *
 * If badge_pdf_url is a Cloudinary CDN URL (https://...) return it directly —
 * the browser can open/download it without any auth header.
 *
 * If it is a local /static/... path (local dev fallback), fetch via the
 * authenticated axios instance, convert to a blob URL, and return that.
 * The caller must call URL.revokeObjectURL(url) when done in the local case.
 *
 * Returns { url, isBlob } so the caller knows whether to revoke.
 */
export async function resolveBadgeUrl(attendeeId, badgePdfUrl) {
  // Cloudinary / any external CDN URL — use directly, no auth needed
  if (badgePdfUrl && (badgePdfUrl.startsWith('https://') || badgePdfUrl.startsWith('http://'))) {
    return { url: badgePdfUrl, isBlob: false }
  }

  // Local /static/... path — must go through the authenticated backend endpoint
  const resp = await api.get(`/attendees/${attendeeId}/badge`, { responseType: 'blob' })
  const blob = new Blob([resp.data], { type: 'application/pdf' })
  return { url: URL.createObjectURL(blob), isBlob: true }
}
