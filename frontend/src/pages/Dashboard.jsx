import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import QRCode from 'react-qr-code'
import toast from 'react-hot-toast'
import { getMyRegistrations, getAttendeeStatus, getBadgeUrl } from '../api/attendees'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import StatusPill from '../components/StatusPill'
import Spinner from '../components/Spinner'
import usePolling from '../hooks/usePolling'

/* ── Single registration card ─────────────────────────────────────────────── */
function RegistrationCard({ reg, onStatusUpdate }) {
  const [showQR, setShowQR] = useState(false)
  const isPending   = reg.status === 'pending'
  const isCheckedIn = reg.status === 'checked_in'
  const badgeUrl    = getBadgeUrl(reg.id)

  // Poll status every 3 s while pending
  const pollStatus = useCallback(async () => {
    try {
      const { data } = await getAttendeeStatus(reg.id)
      if (data.status !== reg.status) {
        onStatusUpdate(reg.id, data.status, data.badge_pdf_url)
      }
    } catch {
      // silently ignore poll errors
    }
  }, [reg.id, reg.status, onStatusUpdate])

  usePolling(pollStatus, 3000, isPending)

  const eventDate = new Date(reg.event?.date ?? reg.event_date)
  const dateLabel = eventDate.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  })

  const handlePrint = () => {
    window.open(badgeUrl, '_blank')
    setTimeout(() => window.print(), 800)
  }

  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden animate-fade-in">
      {/* Card header */}
      <div className="bg-[#1E2A4A] px-5 py-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-orange-400 text-xs font-semibold uppercase tracking-wide mb-0.5">
            {reg.event?.title ?? 'Event'}
          </p>
          <p className="text-white/80 text-sm">{dateLabel}</p>
          {reg.event?.location && (
            <p className="text-white/60 text-xs mt-0.5">{reg.event.location}</p>
          )}
        </div>
        <StatusPill status={reg.status} />
      </div>

      {/* Card body */}
      <div className="px-5 py-4 space-y-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="font-medium text-gray-800">{reg.name}</span>
          {reg.profession && (
            <span className="text-gray-400">· {reg.profession}</span>
          )}
        </div>

        {/* Pending notice */}
        {isPending && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-xs font-medium">
            <Spinner size="sm" className="text-amber-500" />
            Badge is being generated — this page will update automatically.
          </div>
        )}

        {/* Actions row */}
        <div className="flex flex-wrap gap-2 pt-1">
          {/* View QR toggle */}
          <button
            onClick={() => setShowQR(v => !v)}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 hover:border-gray-400
              text-gray-600 hover:text-gray-800 transition-colors font-medium"
          >
            {showQR ? 'Hide QR Code' : 'View QR Code'}
          </button>

          {/* Badge actions — only when checked in */}
          {isCheckedIn && (
            <>
              <a
                href={badgeUrl}
                download
                className="text-xs px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700
                  text-white font-semibold transition-colors"
              >
                Download Badge
              </a>
              <button
                onClick={handlePrint}
                className="text-xs px-3 py-1.5 rounded-lg bg-[#1E2A4A] hover:bg-[#243357]
                  text-white font-semibold transition-colors"
              >
                Print Badge
              </button>
            </>
          )}
        </div>

        {/* QR Code */}
        {showQR && (
          <div className="flex flex-col items-center gap-2 pt-2 pb-1 animate-fade-in">
            <div className="p-3 bg-white border border-gray-200 rounded-xl shadow-sm inline-block">
              <QRCode value={reg.qr_code_id} size={160} />
            </div>
            <p className="text-xs text-gray-400 text-center">
              Present this QR code at the event entrance
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Dashboard page ───────────────────────────────────────────────────────── */
export default function Dashboard() {
  const { user } = useAuth()
  const [registrations, setRegistrations] = useState([])
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState(null)

  useEffect(() => {
    getMyRegistrations()
      .then(r => setRegistrations(r.data))
      .catch(() => setError('Failed to load your registrations. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  // Called by child cards when a poll reveals a status change
  const handleStatusUpdate = useCallback((id, newStatus, badgePdfUrl) => {
    setRegistrations(prev =>
      prev.map(r => r.id === id ? { ...r, status: newStatus, badge_pdf_url: badgePdfUrl } : r)
    )
    if (newStatus === 'checked_in') {
      toast.success('You have been checked in! Your badge is ready.')
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Page header */}
      <div className="bg-[#1E2A4A] py-10 px-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-extrabold text-white">My Dashboard</h1>
          <p className="mt-1 text-gray-400 text-sm">
            Welcome back{user?.email ? `, ${user.email}` : ''}
          </p>
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
        ) : registrations.length === 0 ? (
          <div className="text-center py-24 animate-fade-in">
            <span className="text-6xl">🎟️</span>
            <h2 className="mt-4 text-xl font-bold text-[#1E2A4A]">No registrations yet</h2>
            <p className="mt-2 text-gray-500 text-sm">Browse our events and sign up for one!</p>
            <Link
              to="/events"
              className="inline-block mt-6 px-6 py-3 rounded-xl bg-orange-500 hover:bg-orange-600
                text-white font-semibold text-sm transition-colors"
            >
              Browse Events
            </Link>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-[#1E2A4A]">
                Your Registrations
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({registrations.length})
                </span>
              </h2>
              <Link
                to="/events"
                className="text-sm px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600
                  text-white font-semibold transition-colors"
              >
                Register for Another
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {registrations.map(reg => (
                <RegistrationCard
                  key={reg.id}
                  reg={reg}
                  onStatusUpdate={handleStatusUpdate}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
