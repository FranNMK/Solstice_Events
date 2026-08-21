import { Link } from 'react-router-dom'

/**
 * EventCard — used on the Landing carousel and the Events grid.
 * Shows image, title, date, location, countdown pill, and a Register button.
 */
export default function EventCard({ event, compact = false }) {
  const eventDate  = new Date(event.date)
  const daysAway   = Math.ceil((eventDate - Date.now()) / 86_400_000)
  const isPast     = daysAway < 0
  const dateLabel  = eventDate.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  })

  return (
    <div className={`bg-white rounded-2xl shadow-md overflow-hidden flex flex-col
      hover:shadow-xl transition-shadow duration-300 group
      ${compact ? 'min-w-[280px]' : ''}`}>

      {/* Image */}
      <div className="relative h-44 overflow-hidden bg-gray-100">
        {event.image_url ? (
          <img
            src={event.image_url}
            alt={event.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#1E2A4A] to-[#F97316]">
            <span className="text-white text-4xl">☀</span>
          </div>
        )}

        {/* Countdown pill */}
        <div className="absolute top-3 right-3">
          {isPast ? (
            <span className="bg-gray-700/80 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
              Past
            </span>
          ) : daysAway === 0 ? (
            <span className="bg-orange-500 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
              Today!
            </span>
          ) : (
            <span className="bg-[#1E2A4A]/85 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
              {daysAway}d away
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-col flex-1 p-4 gap-2">
        <h3 className="font-bold text-[#1E2A4A] text-base leading-snug line-clamp-2">
          {event.title}
        </h3>

        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <CalIcon />
          <span>{dateLabel}</span>
        </div>

        {event.location && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <PinIcon />
            <span className="truncate">{event.location}</span>
          </div>
        )}

        {!compact && event.description && (
          <p className="text-sm text-gray-600 line-clamp-2 mt-1">{event.description}</p>
        )}

        <div className="mt-auto pt-3">
          <Link
            to={`/events/${event.id}/register`}
            className="block w-full text-center text-sm font-semibold py-2 px-4 rounded-xl
              bg-[#F97316] hover:bg-orange-600 text-white transition-colors duration-200"
          >
            Register
          </Link>
        </div>
      </div>
    </div>
  )
}

function CalIcon() {
  return (
    <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function PinIcon() {
  return (
    <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}
