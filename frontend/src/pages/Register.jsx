import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getEvent } from '../api/events'
import { registerForEvent } from '../api/attendees'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import Spinner from '../components/Spinner'

export default function Register() {
  const { id: eventId } = useParams()
  const navigate        = useNavigate()
  const { user, isAuthenticated } = useAuth()

  const [event, setEvent]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]   = useState('')
  const [form, setForm]     = useState({ name: '', profession: '' })

  // Prefill name from auth user email (first part)
  useEffect(() => {
    if (user?.email) {
      setForm(f => ({ ...f, name: f.name || user.email.split('@')[0] }))
    }
  }, [user])

  useEffect(() => {
    getEvent(eventId)
      .then(r => setEvent(r.data))
      .catch(() => setError('Event not found.'))
      .finally(() => setLoading(false))
  }, [eventId])

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    if (!isAuthenticated) {
      navigate(`/login?redirect=/events/${eventId}/register`)
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await registerForEvent({ event_id: eventId, name: form.name, profession: form.profession })
      toast.success('Registration successful! Check your email for confirmation.')
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Registration failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-lg mx-auto px-4 py-12">
        {loading ? (
          <div className="flex justify-center py-24"><Spinner size="lg" /></div>
        ) : (
          <>
            {/* Event summary card */}
            {event && (
              <div className="bg-[#1E2A4A] text-white rounded-2xl p-5 mb-6 shadow-lg">
                <p className="text-orange-400 text-xs font-semibold uppercase tracking-wide mb-1">
                  Registering for
                </p>
                <h2 className="text-xl font-extrabold">{event.title}</h2>
                <p className="text-gray-300 text-sm mt-1">
                  {new Date(event.date).toLocaleDateString('en-US', {
                    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                  })}
                  {event.location && ` · ${event.location}`}
                </p>
              </div>
            )}

            {/* Auth gate */}
            {!isAuthenticated ? (
              <div className="bg-white rounded-2xl shadow p-8 text-center">
                <p className="text-gray-600 mb-4">You need an account to register for events.</p>
                <div className="flex gap-3 justify-center">
                  <Link to={`/login?redirect=/events/${eventId}/register`}
                    className="px-5 py-2.5 rounded-xl bg-[#1E2A4A] text-white text-sm font-semibold">
                    Sign In
                  </Link>
                  <Link to="/register"
                    className="px-5 py-2.5 rounded-xl bg-orange-500 text-white text-sm font-semibold">
                    Create Account
                  </Link>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-lg p-8 animate-fade-in">
                <h1 className="text-xl font-extrabold text-[#1E2A4A] mb-6">Your Details</h1>

                {error && (
                  <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text" name="name" required
                      value={form.name} onChange={handleChange}
                      placeholder="Jane Smith"
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-300
                        focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Profession / Role
                    </label>
                    <input
                      type="text" name="profession"
                      value={form.profession} onChange={handleChange}
                      placeholder="e.g. Software Engineer, Designer…"
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-300
                        focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
                    />
                    <p className="text-xs text-gray-400 mt-1">Printed on your badge</p>
                  </div>

                  <div className="pt-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="text" disabled value={user?.email ?? ''}
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-200
                        bg-gray-50 text-gray-500 text-sm cursor-not-allowed"
                    />
                  </div>

                  <button
                    type="submit" disabled={submitting}
                    className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600
                      disabled:opacity-60 text-white font-semibold text-sm transition-colors
                      flex items-center justify-center gap-2 mt-2"
                  >
                    {submitting && <Spinner size="sm" />}
                    {submitting ? 'Registering…' : 'Confirm Registration'}
                  </button>
                </form>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
