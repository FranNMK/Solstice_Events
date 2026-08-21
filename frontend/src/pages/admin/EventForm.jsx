import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getEvent, createEvent, updateEvent } from '../../api/events'
import Navbar from '../../components/Navbar'
import Spinner from '../../components/Spinner'

/* Convert a UTC datetime string from the API into a local datetime-local input value */
function toDatetimeLocal(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export default function EventForm() {
  const { id } = useParams()          // present when editing
  const isEdit  = Boolean(id)
  const navigate = useNavigate()

  const [form, setForm] = useState({
    title: '',
    description: '',
    date: '',
    location: '',
    image_url: '',
    is_published: false,
  })
  const [loading, setLoading]     = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]         = useState('')

  // Load existing event when editing
  useEffect(() => {
    if (!isEdit) return
    getEvent(id)
      .then(r => {
        const ev = r.data
        setForm({
          title:        ev.title       ?? '',
          description:  ev.description ?? '',
          date:         toDatetimeLocal(ev.date),
          location:     ev.location    ?? '',
          image_url:    ev.image_url   ?? '',
          is_published: ev.is_published ?? false,
        })
      })
      .catch(() => setError('Failed to load event.'))
      .finally(() => setLoading(false))
  }, [id, isEdit])

  const handleChange = e => {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        // Convert local datetime-local string to ISO for backend
        date: new Date(form.date).toISOString(),
        description: form.description || null,
        location:    form.location    || null,
        image_url:   form.image_url   || null,
      }

      if (isEdit) {
        await updateEvent(id, payload)
        toast.success('Event updated!')
      } else {
        await createEvent(payload)
        toast.success('Event created!')
      }
      navigate('/admin')
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Failed to save event.'
      setError(Array.isArray(msg) ? msg.map(m => m.msg).join(', ') : msg)
      toast.error('Save failed.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex justify-center py-32"><Spinner size="lg" /></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Header */}
      <div className="bg-[#1E2A4A] py-10 px-6">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <Link to="/admin" className="text-gray-400 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold text-white">
              {isEdit ? 'Edit Event' : 'Create Event'}
            </h1>
            <p className="text-gray-400 text-sm mt-0.5">
              {isEdit ? 'Update event details below' : 'Fill in the details for the new event'}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">
        <div className="bg-white rounded-2xl shadow-md p-8 animate-fade-in">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-400">*</span>
              </label>
              <input
                type="text" name="title" required
                value={form.title} onChange={handleChange}
                placeholder="e.g. Solstice Tech Summit 2025"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                name="description" rows={4}
                value={form.description} onChange={handleChange}
                placeholder="Describe the event…"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm resize-none"
              />
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date & Time <span className="text-red-400">*</span>
              </label>
              <input
                type="datetime-local" name="date" required
                value={form.date} onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text" name="location"
                value={form.location} onChange={handleChange}
                placeholder="e.g. Grand Convention Centre, San Francisco"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            {/* Image URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
              <input
                type="url" name="image_url"
                value={form.image_url} onChange={handleChange}
                placeholder="https://images.unsplash.com/…"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
              {form.image_url && (
                <img
                  src={form.image_url} alt="Preview"
                  className="mt-2 h-24 w-full object-cover rounded-xl border border-gray-200"
                  onError={e => { e.target.style.display = 'none' }}
                />
              )}
            </div>

            {/* Publish toggle */}
            <div className="flex items-center gap-3 pt-1">
              <input
                type="checkbox" id="is_published" name="is_published"
                checked={form.is_published} onChange={handleChange}
                className="w-4 h-4 accent-orange-500"
              />
              <label htmlFor="is_published" className="text-sm font-medium text-gray-700 cursor-pointer">
                Publish immediately (visible to customers)
              </label>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit" disabled={submitting}
                className="flex-1 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-60
                  text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
              >
                {submitting && <Spinner size="sm" />}
                {submitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Event'}
              </button>
              <Link
                to="/admin"
                className="px-5 py-3 rounded-xl border border-gray-300 hover:border-gray-400 text-gray-600 font-semibold text-sm transition-colors text-center"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
