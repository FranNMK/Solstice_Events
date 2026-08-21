import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

// ── Page components ──────────────────────────────────────────────────────────
import Landing        from './pages/Landing'
import Events         from './pages/Events'
import Register       from './pages/Register'
import Login          from './pages/Login'
import SignUp         from './pages/SignUp'
import Dashboard      from './pages/Dashboard'
import AdminDashboard from './pages/admin/AdminDashboard'
import EventForm      from './pages/admin/EventForm'
import AttendeeList   from './pages/admin/AttendeeList'
import ScanPage       from './pages/admin/ScanPage'

const Unauthorized = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-8 text-center">
    <span className="text-6xl mb-4">🔒</span>
    <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
    <p className="mt-2 text-gray-500">You don't have permission to view this page.</p>
    <a href="/" className="mt-6 px-5 py-2 rounded-xl bg-[#1E2A4A] text-white text-sm font-medium">
      Go Home
    </a>
  </div>
)

// ── Route guard ──────────────────────────────────────────────────────────────
function RequireAuth({ children, role }) {
  const { isAuthenticated, user } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role && user?.role !== role) return <Navigate to="/unauthorized" replace />
  return children
}

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: { borderRadius: '12px', fontFamily: 'system-ui, sans-serif', fontSize: '14px' },
            success: { iconTheme: { primary: '#F97316', secondary: '#fff' } },
          }}
        />
        <Routes>
          {/* Public */}
          <Route path="/"                        element={<Landing />} />
          <Route path="/events"                  element={<Events />} />
          <Route path="/events/:id/register"     element={<Register />} />
          <Route path="/login"                   element={<Login />} />
          <Route path="/register"                element={<SignUp />} />
          <Route path="/unauthorized"            element={<Unauthorized />} />

          {/* Customer-protected */}
          <Route path="/dashboard" element={
            <RequireAuth role="customer"><Dashboard /></RequireAuth>
          } />

          {/* Admin-protected */}
          <Route path="/admin" element={
            <RequireAuth role="admin"><AdminDashboard /></RequireAuth>
          } />
          <Route path="/admin/events/new" element={
            <RequireAuth role="admin"><EventForm /></RequireAuth>
          } />
          <Route path="/admin/events/:id/edit" element={
            <RequireAuth role="admin"><EventForm /></RequireAuth>
          } />
          <Route path="/admin/events/:id/attendees" element={
            <RequireAuth role="admin"><AttendeeList /></RequireAuth>
          } />
          <Route path="/admin/scan" element={
            <RequireAuth role="admin"><ScanPage /></RequireAuth>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
