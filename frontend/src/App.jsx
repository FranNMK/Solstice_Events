import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

// ── Placeholder page components (replaced in later phases) ──────────────────
const Landing = () => <div className="p-8"><h1>Landing Page</h1></div>
const Events = () => <div className="p-8"><h1>Events</h1></div>
const Register = () => <div className="p-8"><h1>Register for Event</h1></div>
const Login = () => <div className="p-8"><h1>Login</h1></div>
const SignUp = () => <div className="p-8"><h1>Sign Up</h1></div>
const Dashboard = () => <div className="p-8"><h1>Customer Dashboard</h1></div>
const AdminDashboard = () => <div className="p-8"><h1>Admin Dashboard</h1></div>
const EventForm = () => <div className="p-8"><h1>Event Form</h1></div>
const AttendeeList = () => <div className="p-8"><h1>Attendee List</h1></div>
const ScanPage = () => <div className="p-8"><h1>Scan Page</h1></div>
const Unauthorized = () => (
  <div className="p-8 text-center">
    <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
    <p className="mt-2 text-gray-600">You do not have permission to view this page.</p>
  </div>
)

// ── Route guard ──────────────────────────────────────────────────────────────
function RequireAuth({ children, role }) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role && user?.role !== role) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          {/* Public */}
          <Route path="/" element={<Landing />} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:id/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<SignUp />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Customer-protected */}
          <Route
            path="/dashboard"
            element={
              <RequireAuth role="customer">
                <Dashboard />
              </RequireAuth>
            }
          />

          {/* Admin-protected */}
          <Route
            path="/admin"
            element={
              <RequireAuth role="admin">
                <AdminDashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/admin/events/new"
            element={
              <RequireAuth role="admin">
                <EventForm />
              </RequireAuth>
            }
          />
          <Route
            path="/admin/events/:id/edit"
            element={
              <RequireAuth role="admin">
                <EventForm />
              </RequireAuth>
            }
          />
          <Route
            path="/admin/events/:id/attendees"
            element={
              <RequireAuth role="admin">
                <AttendeeList />
              </RequireAuth>
            }
          />
          <Route
            path="/admin/scan"
            element={
              <RequireAuth role="admin">
                <ScanPage />
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
