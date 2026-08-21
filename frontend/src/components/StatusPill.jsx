/**
 * StatusPill — coloured badge for attendee status
 * registered  → gray
 * pending     → amber
 * checked_in  → green
 */
export default function StatusPill({ status }) {
  const map = {
    registered: 'bg-gray-100 text-gray-600 border border-gray-300',
    pending:    'bg-amber-100 text-amber-700 border border-amber-300',
    checked_in: 'bg-green-100 text-green-700 border border-green-300',
  }
  const label = {
    registered: 'Registered',
    pending:    'Pending…',
    checked_in: 'Checked In ✓',
  }
  const cls = map[status] ?? 'bg-gray-100 text-gray-500 border border-gray-200'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {label[status] ?? status}
    </span>
  )
}
