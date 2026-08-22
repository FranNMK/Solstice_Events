import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import QRCode from 'react-qr-code'
import toast from 'react-hot-toast'
import { getMyRegistrations, getAttendeeStatus, resolveBadgeUrl, unregisterAttendee } from '../api/attendees'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import StatusPill from '../components/StatusPill'
import Spinner from '../components/Spinner'
import usePolling from '../hooks/usePolling'

/* ── Confirm unregister modal ─────────────────────────────────────────────── */
function UnregisterModal({ eventTitle, onConfirm, onCancel, loading }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.45)' }}>
      <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-6 animate-fade-in">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-3xl">🚫</span>
          <div>
            <h3 className="font-extrabold text-[#1E2A4A] text-lg">Unregister?</h3>
            <p className="text-xs text-gray-500 mt-0.5">This cannot be undone.</p>
          </div>
        </div>
        <p className="text-sm text-gray-700 mb-5">
          Cancel your registration for <span className="font-semibold">"{eventTitle}"</span>?
          You can re-register later if spots are still available.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-60
              text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading && <Spinner size="sm" />}
            {loading ? 'Cancelling…' : 'Yes, Unregister'}
          </button>
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl border border-gray-300 hover:border-gray-400
              text-gray-700 font-semibold text-sm transition-colors disabled:opacity-60"
          >
            Keep Registration
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Single registration card ─────────────────────────────────────────────── */
function RegistrationCard({ reg, onStatusUpdate, onUnregister }) {
  const [showQR, setShowQR]               = useState(false)
  const [confirmUnreg, setConfirmUnreg]   = useState(false)
  const [unregistering, setUnregistering] = useState(false)
  const [badgeLoading, setBadgeLoading]   = useState(false)

  const isPending    = reg.status === 'pending'
  const isCheckedIn  = reg.status === 'checked_in'
  const isRegistered = reg.status === 'registered'

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

  // Resolve the badge URL (CDN direct or blob fallback) then trigger download
  const handleDownload = async () => {
    setBadgeLoading(true)
    try {
      const { url, isBlob } = await resolveBadgeUrl(reg.id, reg.badge_pdf_url)
      const a = document.createElement('a')
      a.href = url
      a.download = `badge-${reg.name.replace(/\s+/g, '_')}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      if (isBlob) URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download badge. Please try again.')
    } finally {
      setBadgeLoading(false)
    }
  }

  // Resolve the badge URL then open in a new tab for printing
  const handlePrint = async () => {
    setBadgeLoading(true)
    try {
      const { url, isBlob } = await resolveBadgeUrl(reg.id, reg.badge_pdf_url)
      const win = window.open(url, '_blank')
      if (isBlob) setTimeout(() => URL.revokeObjectURL(url), 30_000)
      if (!win) toast('Allow pop-ups to print the badge.', { icon: 'ℹ️' })
    } catch {
      toast.error('Failed to open badge for printing. Please try again.')
    } finally {
      setBadgeLoading(false)
    }
  }

  const handleUnregister = async () => {
    setUnregistering(true)
    try {
      await unregisterAttendee(reg.id)
      onUnregister(reg.id)
      toast.success('Registration cancelled.')
      setConfirmUnreg(false)
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Failed to unregister.'
      toast.error(msg)
      setUnregistering(false)
      setConfirmUnreg(false)
    }
  }

  return (
    <>
      {confirmUnreg && (
        <UnregisterModal
          eventTitle={reg.event?.title ?? 'this event'}
          onConfirm={handleUnregister}
          onCancel={() => setConfirmUnreg(false)}
          loading={unregistering}
        />
      )}

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
                <button
                  onClick={handleDownload}
                  disabled={badgeLoading}
                  className="text-xs px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700
                    disabled:opacity-60 text-white font-semibold transition-colors
                    flex items-center gap-1.5"
                >
                  {badgeLoading && <Spinner size="sm" />}
                  Download Badge
                </button>
                <button
                  onClick={handlePrint}
                  disabled={badgeLoading}
                  className="text-xs px-3 py-1.5 rounded-lg bg-[#1E2A4A] hover:bg-[#243357]
                    disabled:opacity-60 text-white font-semibold transition-colors
                    flex items-center gap-1.5"
                >
                  {badgeLoading && <Spinner size="sm" />}
                  Print Badge
                </button>
              </>
            )}

            {/* Unregister — only while status is 'registered' */}
            {isRegistered && (
              <button
                onClick={() => setConfirmUnreg(true)}
                className="text-xs px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100
                  text-red-600 border border-red-200 font-semibold transition-colors"
              >
                Unregister
              </button>
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
    </>
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

  const handleStatusUpdate = useCallback((id, newStatus, badgePdfUrl) => {
    setRegistrations(prev =>
      prev.map(r => r.id === id ? { ...r, status: newStatus, badge_pdf_url: badgePdfUrl } : r)
    )
    if (newStatus === 'checked_in') {
      toast.success('You have been checked in! Your badge is ready.')
    }
  }, [])

  const handleUnregister = useCallback((id) => {
    setRegistrations(prev => prev.filter(r => r.id !== id))
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
                  onUnregister={handleUnregister}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
