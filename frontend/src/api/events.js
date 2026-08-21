import api from './index'

export const getEvents       = ()         => api.get('/events')
export const getEvent        = (id)       => api.get(`/events/${id}`)
export const getAdminEvents  = ()         => api.get('/admin/events')
export const createEvent     = (data)     => api.post('/admin/events', data)
export const updateEvent     = (id, data) => api.put(`/admin/events/${id}`, data)
export const getEventAttendees = (id)     => api.get(`/admin/events/${id}/attendees`)
