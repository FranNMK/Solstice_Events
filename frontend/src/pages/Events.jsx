import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getEvents } from '../api/events'
import EventCard from '../components/EventCard'
import Navbar from '../components/Navbar'
import Spinner from '../components/Spinner'

export default function Events() {
  const [events, setEvents]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    getEvents()
      .then(r  => setEvents(r.data))
      .catch(() => setError('Failed to load events. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Page header */}
      <div className="bg-[#1E2A4A] py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-extrabold text-white">All Events</h1>
          <p className="mt-2 text-gray-400">Browse and register for upcoming events</p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
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
          <div className="text-center py-24">
            <span className="text-5xl">📅</span>
            <p className="mt-4 text-gray-500 font-medium">No upcoming events at the moment.</p>
            <p className="text-gray-400 text-sm mt-1">Check back soon!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map(ev => <EventCard key={ev.id} event={ev} />)}
          </div>
        )}
      </div>
    </div>
  )
}
