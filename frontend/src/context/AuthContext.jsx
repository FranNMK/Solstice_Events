import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

/**
 * Decode the payload from a JWT without verifying the signature.
 * Returns {id, role, email, exp} or null on error.
 */
function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return {
      id: decoded.sub,
      role: decoded.role,
      email: decoded.email,
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('token')
    return stored ? decodeToken(stored) : null
  })

  function login(newToken) {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    setUser(decodeToken(newToken))
  }

  function logout() {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const isAuthenticated = Boolean(token) && Boolean(user)

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
