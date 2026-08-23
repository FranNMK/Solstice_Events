import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getEventAttendees, getEvent } from '../../api/events'
import Navbar from '../../components/Navbar'
import StatusPill from '../../components/StatusPill'
import Spinner from '../../components/Spinner'

export default function AttendeeList() {
  const { id: eventId } = useParams()
  const [event, setEvent]         = useState(null)
  const [attendees, setAttendees] = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    Promise.all([
      getEvent(eventId),
      getEventAttendees(eventId),
    ])
      .then(([evRes, attRes]) => {
        setEvent(evRes.data)
        setAttendees(attRes.data)
      })
      .catch(() => setError('Failed to load attendees.'))
      .finally(() => setLoading(false))
  }, [eventId])

  const checkedIn  = attendees.filter(a => a.status === 'checked_in').length
  const pending    = attendees.filter(a => a.status === 'pending').length
  const registered = attendees.filter(a => a.status === 'registered').length

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Header */}
      <div className="bg-[#1E2A4A] py-10 px-6">
        <div className="max-w-5xl mx-auto">
          <Link to="/admin" className="inline-flex items-center gap-1.5 text-gray-400 hover:text-white text-sm mb-3 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </Link>
          <h1 className="text-2xl font-extrabold text-white">
            {event ? event.title : 'Attendees'}
          </h1>
          {event && (
            <p className="text-gray-400 text-sm mt-1">
              {new Date(event.date).toLocaleDateString('en-US', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
              })}
              {event.location && ` · ${event.location}`}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-10">
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
        ) : (
          <>
            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              {[
                { label: 'Total',       value: attendees.length,  color: 'text-[#1E2A4A]' },
                { label: 'Registered',  value: registered,        color: 'text-gray-600' },
                { label: 'Pending',     value: pending,           color: 'text-amber-600' },
                { label: 'Checked In',  value: checkedIn,         color: 'text-green-600' },
              ].map(s => (
                <div key={s.label} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 text-center">
                  <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
                  <p className="text-xs text-gray-500 mt-0.5 font-medium">{s.label}</p>
                </div>
              ))}
            </div>

            {attendees.length === 0 ? (
              <div className="text-center py-20">
                <span className="text-5xl">👥</span>
                <p className="mt-4 text-gray-500 font-medium">No attendees registered yet.</p>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-100">
                        <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Name</th>
                        <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Profession</th>
                        <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Status</th>
                        <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Badge</th>
                        <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Registered</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {attendees.map(a => (
                        <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-5 py-3 font-medium text-[#1E2A4A]">{a.name}</td>
                          <td className="px-5 py-3 text-gray-500">{a.profession || '—'}</td>
                          <td className="px-5 py-3"><StatusPill status={a.status} /></td>
                          <td className="px-5 py-3">
                            {a.status === 'checked_in' && a.badge_pdf_url ? (
                              <a
                                href={a.badge_pdf_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                download
                                className="text-xs px-2.5 py-1 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold transition-colors"
                              >
                                Download
                              </a>
                            ) : (
                              <span className="text-gray-300 text-xs">—</span>
                            )}
                          </td>
                          <td className="px-5 py-3 text-gray-400 text-xs">
                            {new Date(a.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
