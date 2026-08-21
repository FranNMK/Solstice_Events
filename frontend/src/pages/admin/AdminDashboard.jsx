import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getAdminEvents, updateEvent } from '../../api/events'
import Navbar from '../../components/Navbar'
import Spinner from '../../components/Spinner'

/* ── Helpers ───────────────────────────────────────────────────────────────── */
function formatDate(dt) {
  return new Date(dt).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  })
}

/* ── Event row card ─────────────────────────────────────────────────────────── */
function EventRow({ event, onTogglePublish }) {
  const [toggling, setToggling] = useState(false)

  const handleToggle = async () => {
    setToggling(true)
    try {
      await onTogglePublish(event.id, !event.is_published)
    } finally {
      setToggling(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 flex flex-col sm:flex-row sm:items-center gap-4 hover:shadow-md transition-shadow">
      {/* Image thumbnail */}
      <div className="w-full sm:w-20 h-20 rounded-xl overflow-hidden bg-gradient-to-br from-[#1E2A4A] to-orange-500 shrink-0">
        {event.image_url ? (
          <img src={event.image_url} alt={event.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white text-2xl">☀</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <h3 className="font-bold text-[#1E2A4A] text-base truncate">{event.title}</h3>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            event.is_published
              ? 'bg-green-100 text-green-700 border border-green-300'
              : 'bg-gray-100 text-gray-500 border border-gray-300'
          }`}>
            {event.is_published ? 'Published' : 'Draft'}
          </span>
        </div>
        <p className="text-xs text-gray-500">{formatDate(event.date)}</p>
        {event.location && <p className="text-xs text-gray-400 truncate">{event.location}</p>}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 shrink-0">
        <Link
          to={`/admin/events/${event.id}/attendees`}
          className="text-xs px-3 py-1.5 rounded-lg bg-[#1E2A4A] hover:bg-[#243357] text-white font-semibold transition-colors"
        >
          Attendees
        </Link>
        <Link
          to={`/admin/events/${event.id}/edit`}
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 hover:border-gray-400 text-gray-700 font-semibold transition-colors"
        >
          Edit
        </Link>
        <button
          onClick={handleToggle}
          disabled={toggling}
          className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-60 ${
            event.is_published
              ? 'bg-amber-100 text-amber-700 hover:bg-amber-200 border border-amber-300'
              : 'bg-orange-500 text-white hover:bg-orange-600'
          }`}
        >
          {toggling ? '…' : event.is_published ? 'Unpublish' : 'Publish'}
        </button>
      </div>
    </div>
  )
}

/* ── Admin Dashboard ────────────────────────────────────────────────────────── */
export default function AdminDashboard() {
  const [events, setEvents]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getAdminEvents()
      .then(r => setEvents(r.data))
      .catch(() => setError('Failed to load events.'))
      .finally(() => setLoading(false))
  }, [])

  const handleTogglePublish = async (id, newPublished) => {
    try {
      const { data } = await updateEvent(id, { is_published: newPublished })
      setEvents(prev => prev.map(e => e.id === id ? data : e))
      toast.success(newPublished ? 'Event published!' : 'Event unpublished.')
    } catch {
      toast.error('Failed to update event.')
    }
  }

  const published = events.filter(e => e.is_published).length
  const drafts    = events.length - published

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Header */}
      <div className="bg-[#1E2A4A] py-10 px-6">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-white">Admin Dashboard</h1>
            <p className="mt-1 text-gray-400 text-sm">Manage events, attendees, and check-ins</p>
          </div>
          <div className="flex gap-3">
            <Link
              to="/admin/scan"
              className="px-4 py-2 rounded-xl border border-orange-400 text-orange-400 hover:bg-orange-500 hover:text-white font-semibold text-sm transition-colors"
            >
              Scan QR
            </Link>
            <Link
              to="/admin/events/new"
              className="px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm transition-colors"
            >
              + Create Event
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Stats row */}
        {!loading && !error && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Total Events', value: events.length },
              { label: 'Published',    value: published },
              { label: 'Drafts',       value: drafts },
            ].map(s => (
              <div key={s.label} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
                <p className="text-3xl font-extrabold text-[#1E2A4A]">{s.value}</p>
                <p className="text-xs text-gray-500 mt-1 font-medium">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-24"><Spinner size="lg" /></div>
        ) : error ? (
          <div className="text-center py-24">
            <p className="text-red-500 font-medium">{error}</p>
            <button onClick={() => window.location.reload()}
              className="mt-4 px-5 py-2 rounded-lg bg-[#1E2A4A] text-white text-sm font-medium">
              Retry
            </button>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-24 animate-fade-in">
            <span className="text-6xl">📅</span>
            <h2 className="mt-4 text-xl font-bold text-[#1E2A4A]">No events yet</h2>
            <p className="mt-2 text-gray-500 text-sm">Create your first event to get started.</p>
            <button
              onClick={() => navigate('/admin/events/new')}
              className="mt-6 inline-block px-6 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm transition-colors"
            >
              Create Event
            </button>
          </div>
        ) : (
          <>
            <h2 className="text-lg font-bold text-[#1E2A4A] mb-4">
              All Events <span className="text-sm font-normal text-gray-500">({events.length})</span>
            </h2>
            <div className="space-y-3">
              {events.map(ev => (
                <EventRow key={ev.id} event={ev} onTogglePublish={handleTogglePublish} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
