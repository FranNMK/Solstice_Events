import { useAuth as _useAuth } from '../context/AuthContext'

/**
 * Convenience hook — re-exports useAuth from AuthContext so pages/components
 * can import from `../hooks/useAuth` instead of `../context/AuthContext`.
 */
export function useAuth() {
  return _useAuth()
}

export default useAuth
