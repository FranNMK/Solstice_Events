import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { getEvents } from '../api/events'
import EventCard from '../components/EventCard'
import Navbar from '../components/Navbar'
import Spinner from '../components/Spinner'

/* ── Hero section ─────────────────────────────────────────────────────────── */
function Hero() {
  return (
    <section className="relative min-h-[88vh] flex items-center justify-center overflow-hidden
      bg-gradient-to-br from-[#1E2A4A] via-[#243357] to-[#1a2240]">

      {/* Decorative circles */}
      <div className="absolute top-[-80px] right-[-80px] w-[420px] h-[420px]
        rounded-full bg-orange-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-60px] left-[-60px] w-[320px] h-[320px]
        rounded-full bg-orange-400/10 blur-2xl pointer-events-none" />

      <div className="relative z-10 text-center px-6 max-w-3xl mx-auto animate-fade-in">
        <img src="/logo.png" alt="Solstice Events" className="h-24 mx-auto mb-8 drop-shadow-xl" />

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white leading-tight">
          Where Moments<br />
          <span className="text-orange-400">Become Memories</span>
        </h1>

        <p className="mt-5 text-lg text-gray-300 max-w-xl mx-auto">
          Discover world-class events, register in seconds, and experience the future of event check-in.
        </p>

        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <Link
            to="/events"
            className="px-8 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white
              font-semibold text-base transition-all duration-200 shadow-lg hover:shadow-orange-500/30"
          >
            Browse Events
          </Link>
          <Link
            to="/register"
            className="px-8 py-3 rounded-xl border border-white/30 hover:border-white/60
              text-white font-semibold text-base transition-all duration-200 hover:bg-white/5"
          >
            Create Account
          </Link>
        </div>

        {/* Tagline pills */}
        <div className="mt-10 flex flex-wrap gap-3 justify-center">
          {['Connect', 'Experience', 'Celebrate'].map(t => (
            <span key={t}
              className="px-4 py-1.5 rounded-full bg-white/10 text-white/80 text-sm font-medium
                border border-white/10">
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Scroll hint */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </section>
  )
}

/* ── Carousel ─────────────────────────────────────────────────────────────── */
function Carousel({ events }) {
  const [idx, setIdx] = useState(0)
  const timerRef = useRef(null)

  const goTo = (i) => setIdx((i + events.length) % events.length)

  useEffect(() => {
    timerRef.current = setInterval(() => setIdx(p => (p + 1) % events.length), 5000)
    return () => clearInterval(timerRef.current)
  }, [events.length])

  if (!events.length) return null

  return (
    <div className="relative overflow-hidden rounded-2xl shadow-xl">
      {/* Slides */}
      <div
        className="flex transition-transform duration-500 ease-in-out"
        style={{ transform: `translateX(-${idx * 100}%)` }}
      >
        {events.map(ev => (
          <div key={ev.id} className="min-w-full">
            <EventCard event={ev} />
          </div>
        ))}
      </div>

      {/* Prev / Next */}
      {events.length > 1 && (
        <>
          <button onClick={() => goTo(idx - 1)}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white
              rounded-full p-1.5 shadow transition-all">
            <svg className="w-4 h-4 text-[#1E2A4A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button onClick={() => goTo(idx + 1)}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white
              rounded-full p-1.5 shadow transition-all">
            <svg className="w-4 h-4 text-[#1E2A4A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </>
      )}

      {/* Dots */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
        {events.map((_, i) => (
          <button key={i} onClick={() => goTo(i)}
            className={`w-2 h-2 rounded-full transition-all ${i === idx ? 'bg-orange-500 w-4' : 'bg-white/60'}`}
          />
        ))}
      </div>
    </div>
  )
}

/* ── Landing page ─────────────────────────────────────────────────────────── */
export default function Landing() {
  const [events, setEvents]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEvents()
      .then(r => setEvents(r.data.slice(0, 5)))   // up to 5 in carousel
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero />

      {/* Featured events carousel */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-extrabold text-[#1E2A4A]">Upcoming Events</h2>
            <p className="mt-2 text-gray-500">Don't miss what's coming next</p>
          </div>

          {loading ? (
            <div className="flex justify-center py-12"><Spinner size="lg" /></div>
          ) : events.length ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map(ev => <EventCard key={ev.id} event={ev} />)}
            </div>
          ) : (
            <p className="text-center text-gray-400 py-12">No upcoming events yet.</p>
          )}

          <div className="text-center mt-10">
            <Link
              to="/events"
              className="inline-block px-8 py-3 rounded-xl bg-[#1E2A4A] hover:bg-[#243357]
                text-white font-semibold transition-colors duration-200"
            >
              View All Events
            </Link>
          </div>
        </div>
      </section>

      {/* Why Solstice */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-3xl font-extrabold text-[#1E2A4A] mb-4">Why Solstice Events?</h2>
          <p className="text-gray-500 mb-12 max-w-xl mx-auto">
            Everything you need for a seamless event experience — from registration to badge pickup.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {[
              { icon: '🎟️', title: 'Instant Registration', desc: 'Sign up for events in seconds and receive your confirmation with QR code immediately.' },
              { icon: '📲', title: 'QR Check-in', desc: 'Present your QR code at the door. No printing needed, no queues.' },
              { icon: '🏷️', title: 'Digital Badges', desc: 'Your personalised badge is ready to download and print right after check-in.' },
            ].map(f => (
              <div key={f.title} className="flex flex-col items-center gap-3 p-6 rounded-2xl
                bg-gray-50 hover:bg-orange-50 transition-colors duration-200">
                <span className="text-4xl">{f.icon}</span>
                <h3 className="font-bold text-[#1E2A4A] text-lg">{f.title}</h3>
                <p className="text-gray-500 text-sm">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#1E2A4A] text-white/60 text-sm py-8 text-center">
        <img src="/logo.png" alt="Solstice Events" className="h-8 mx-auto mb-3 opacity-70" />
        <p>© {new Date().getFullYear()} Solstice Events · Connect · Experience · Celebrate</p>
      </footer>
    </div>
  )
}
