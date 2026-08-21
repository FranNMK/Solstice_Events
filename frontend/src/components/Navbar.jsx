import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()

  return (
    <nav
      style={{ backgroundColor: '#1E2A4A' }}
      className="w-full px-6 py-3 flex items-center justify-between shadow-md"
    >
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2">
        <img src="/logo.png" alt="Solstice Events" className="h-9 w-auto" />
      </Link>

      {/* Centre nav links */}
      <div className="flex items-center gap-6">
        <NavLink
          to="/events"
          className={({ isActive }) =>
            `text-sm font-medium transition-colors ${
              isActive ? 'text-orange-400' : 'text-gray-200 hover:text-white'
            }`
          }
        >
          Events
        </NavLink>

        {isAuthenticated && user?.role === 'customer' && (
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `text-sm font-medium transition-colors ${
                isActive ? 'text-orange-400' : 'text-gray-200 hover:text-white'
              }`
            }
          >
            Dashboard
          </NavLink>
        )}

        {isAuthenticated && user?.role === 'admin' && (
          <>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive ? 'text-orange-400' : 'text-gray-200 hover:text-white'
                }`
              }
            >
              Admin
            </NavLink>
            <NavLink
              to="/admin/scan"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive ? 'text-orange-400' : 'text-gray-200 hover:text-white'
                }`
              }
            >
              Scan
            </NavLink>
          </>
        )}
      </div>

      {/* Right side: auth */}
      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            <span className="text-sm text-gray-300 hidden sm:block">
              {user?.email}
            </span>
            <button
              onClick={logout}
              className="text-sm px-4 py-1.5 rounded bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="text-sm text-gray-200 hover:text-white font-medium transition-colors"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="text-sm px-4 py-1.5 rounded bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors"
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}
