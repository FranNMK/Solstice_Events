import { useState, useEffect, useRef, useCallback } from 'react'
import toast from 'react-hot-toast'
import { checkIn, getAttendeeStatus } from '../../api/attendees'
import Navbar from '../../components/Navbar'
import StatusPill from '../../components/StatusPill'
import Spinner from '../../components/Spinner'
import usePolling from '../../hooks/usePolling'

/* ── Scanned result row ─────────────────────────────────────────────────────── */
function ScanResultRow({ item, onStatusUpdate }) {
  const isPending = item.status === 'pending'

  const pollStatus = useCallback(async () => {
    try {
      const { data } = await getAttendeeStatus(item.attendee_id)
      if (data.status !== item.status) {
        onStatusUpdate(item.attendee_id, data.status, data.badge_pdf_url)
      }
    } catch {
      // ignore poll errors silently
    }
  }, [item.attendee_id, item.status, onStatusUpdate])

  usePolling(pollStatus, 3000, isPending)

  return (
    <div className={`rounded-xl border p-4 flex flex-wrap items-center gap-3 transition-all ${
      item.already_checked_in
        ? 'bg-amber-50 border-amber-300'
        : item.status === 'checked_in'
          ? 'bg-green-50 border-green-300'
          : 'bg-white border-gray-200'
    }`}>
      {/* Identity */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-[#1E2A4A] text-sm truncate">
          {item.name || item.attendee_id}
        </p>
        {item.profession && (
          <p className="text-xs text-gray-500">{item.profession}</p>
        )}
        <p className="text-xs text-gray-400 font-mono mt-0.5 truncate">{item.attendee_id}</p>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 shrink-0">
        {item.already_checked_in ? (
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-300">
            Already checked in
          </span>
        ) : (
          <>
            <StatusPill status={item.status} />
            {isPending && <Spinner size="sm" />}
          </>
        )}
      </div>

      {/* Badge link once checked in */}
      {item.status === 'checked_in' && !item.already_checked_in && item.badge_pdf_url && (
        <a
          href={item.badge_pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          download
          className="text-xs px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold transition-colors shrink-0"
        >
          Download Badge
        </a>
      )}
    </div>
  )
}

/* ── Scan Page ──────────────────────────────────────────────────────────────── */
export default function ScanPage() {
  const videoRef       = useRef(null)
  const readerRef      = useRef(null)
  const scanningRef    = useRef(false)

  const [results, setResults]         = useState([])
  const [manualInput, setManualInput] = useState('')
  const [cameraActive, setCameraActive] = useState(false)
  const [cameraError, setCameraError]   = useState('')
  const [processing, setProcessing]     = useState(false)

  /* ── Handle a decoded QR value (from camera or manual) ─────────────────── */
  const handleQrValue = useCallback(async (qrCodeId) => {
    const trimmed = qrCodeId.trim()
    if (!trimmed) return

    // Debounce: skip if already in results list (same attendee_id pending or done)
    setResults(prev => {
      const alreadyInList = prev.some(r => r.qr_code_id === trimmed)
      if (alreadyInList) return prev
      return prev
    })

    setProcessing(true)
    try {
      const { data } = await checkIn(trimmed)

      if (data.already_checked_in) {
        setResults(prev => {
          // Avoid duplicate entries in the list
          if (prev.some(r => r.attendee_id === data.attendee_id && r.already_checked_in)) return prev
          return [{
            qr_code_id: trimmed,
            attendee_id: data.attendee_id,
            name: null,
            profession: null,
            status: data.status,
            already_checked_in: true,
          }, ...prev]
        })
        toast(data.message || 'Already checked in', { icon: '⚠️' })
      } else {
        setResults(prev => [{
          qr_code_id: trimmed,
          attendee_id: data.attendee_id,
          name: null,
          profession: null,
          status: 'pending',
          already_checked_in: false,
        }, ...prev])
        toast.success('Check-in accepted — badge generating…')
      }
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Check-in failed.'
      toast.error(msg)
    } finally {
      setProcessing(false)
    }
  }, [])

  /* ── Update a result row when polling finds a new status ───────────────── */
  const handleStatusUpdate = useCallback((attendeeId, newStatus, badgePdfUrl) => {
    setResults(prev =>
      prev.map(r =>
        r.attendee_id === attendeeId
          ? { ...r, status: newStatus, badge_pdf_url: badgePdfUrl }
          : r
      )
    )
    if (newStatus === 'checked_in') {
      toast.success('Attendee checked in! Badge ready.')
    }
  }, [])

  /* ── Camera scanner ──────────────────────────────────────────────────────── */
  const startCamera = useCallback(async () => {
    setCameraError('')
    setCameraActive(false)

    // Step 1 — request permission explicitly so the browser dialog fires immediately
    let permStream
    try {
      permStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
      })
    } catch (err) {
      const isDenied = err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError'
      setCameraError(
        isDenied
          ? 'Camera permission was denied. Allow camera access in your browser settings, then try again.'
          : 'No camera found on this device. Use manual entry below.'
      )
      return
    }

    // Step 2 — hand the live stream directly to the video element so ZXing
    // can decode from it without opening a second stream (avoids device-busy errors)
    try {
      const { BrowserQRCodeReader } = await import('@zxing/library')
      const reader = new BrowserQRCodeReader()
      readerRef.current = reader

      // Attach the already-open stream to the video element
      const video = videoRef.current
      video.srcObject = permStream
      await video.play()

      setCameraActive(true)
      scanningRef.current = true

      // Decode frames continuously from the live video element
      reader.decodeFromStream(permStream, video, (result) => {
        if (!scanningRef.current) return
        if (result) {
          handleQrValue(result.getText())
          // Brief pause to avoid re-scanning the same code repeatedly
          scanningRef.current = false
          setTimeout(() => { scanningRef.current = true }, 2500)
        }
      })
    } catch (err) {
      // Stop the permission stream if ZXing failed to start
      permStream?.getTracks().forEach(t => t.stop())
      console.error('Scanner start error:', err)
      setCameraError('Failed to start scanner. Use manual entry below.')
      setCameraActive(false)
    }
  }, [handleQrValue])

  const stopCamera = useCallback(() => {
    scanningRef.current = false
    if (readerRef.current) {
      try { readerRef.current.reset() } catch { /* ignore */ }
      readerRef.current = null
    }
    // Stop any live tracks still attached to the video element
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(t => t.stop())
      videoRef.current.srcObject = null
    }
    setCameraActive(false)
  }, [])

  // Clean up on unmount
  useEffect(() => () => stopCamera(), [stopCamera])

  const handleManualSubmit = e => {
    e.preventDefault()
    handleQrValue(manualInput)
    setManualInput('')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Header */}
      <div className="bg-[#1E2A4A] py-10 px-6">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-extrabold text-white">QR Check-in Scanner</h1>
          <p className="text-gray-400 text-sm mt-1">
            Scan attendee QR codes to check them in
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        {/* Camera section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-bold text-[#1E2A4A]">Camera Scanner</h2>
            {!cameraActive ? (
              <button
                onClick={startCamera}
                className="text-sm px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold transition-colors"
              >
                Start Camera
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="text-sm px-4 py-2 rounded-xl bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold transition-colors"
              >
                Stop Camera
              </button>
            )}
          </div>

          {cameraError && (
            <div className="m-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm">
              {cameraError}
            </div>
          )}

          <div className={`relative bg-black ${cameraActive ? 'block' : 'hidden'}`} style={{ aspectRatio: '4/3', maxHeight: '340px' }}>
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              autoPlay
              muted
              playsInline
            />
            {/* Scan overlay guide */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-48 h-48 border-2 border-orange-400 rounded-2xl opacity-80" />
            </div>
          </div>

          {!cameraActive && !cameraError && (
            <div className="p-10 text-center text-gray-400">
              <span className="text-5xl block mb-2">📷</span>
              <p className="text-sm font-medium text-gray-600">Click "Start Camera" to begin scanning</p>
              <p className="text-xs mt-1">Your browser will ask for camera permission — click <strong>Allow</strong></p>
              <p className="text-xs mt-0.5">Requires HTTPS or localhost</p>
            </div>
          )}
        </div>

        {/* Manual input */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-bold text-[#1E2A4A] mb-3">Manual Entry</h2>
          <form onSubmit={handleManualSubmit} className="flex gap-2">
            <input
              type="text"
              value={manualInput}
              onChange={e => setManualInput(e.target.value)}
              placeholder="Paste QR code ID here…"
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm font-mono"
            />
            <button
              type="submit"
              disabled={!manualInput.trim() || processing}
              className="px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-semibold text-sm transition-colors flex items-center gap-2 shrink-0"
            >
              {processing && <Spinner size="sm" />}
              Check In
            </button>
          </form>
        </div>

        {/* Results list */}
        {results.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-[#1E2A4A]">
                Scan Results <span className="text-sm font-normal text-gray-500">({results.length})</span>
              </h2>
              <button
                onClick={() => setResults([])}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              >
                Clear all
              </button>
            </div>
            {results.map((item, i) => (
              <ScanResultRow
                key={`${item.attendee_id}-${i}`}
                item={item}
                onStatusUpdate={handleStatusUpdate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
