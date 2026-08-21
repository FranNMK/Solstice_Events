import api from './index'

export const registerForEvent = (data)        => api.post('/attendees/register', data)
export const getMyRegistrations = ()          => api.get('/attendees/my')
export const getAttendeeStatus = (id)         => api.get(`/attendees/${id}/status`)
export const getBadgeUrl       = (id)         => `${import.meta.env.VITE_API_URL}/attendees/${id}/badge`
export const checkIn           = (qr_code_id) => api.post('/checkin', { qr_code_id })
