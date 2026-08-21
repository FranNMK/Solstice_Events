import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { login as loginApi } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import Spinner from '../components/Spinner'

function EyeIcon({ open }) {
  return open ? (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ) : (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.97 9.97 0 012.002-3.462M6.228 6.228A9.969 9.969 0 0112 5c4.477 0 8.268 2.943 9.542 7a9.97 9.97 0 01-1.57 2.972M6.228 6.228L3 3m3.228 3.228l3.65 3.65M17.772 17.772l3.228 3.228m-3.228-3.228l-3.65-3.65" />
    </svg>
  )
}

export default function Login() {
  const { login } = useAuth()
  const navigate  = useNavigate()

  const [form, setForm]         = useState({ email: '', password: '' })
  const [showPwd, setShowPwd]   = useState(false)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await loginApi(form)
      login(data.access_token)
      toast.success('Welcome back!')
      navigate(data.role === 'admin' ? '/admin' : '/dashboard', { replace: true })
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Login failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex items-center justify-center py-16 px-4">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8 animate-fade-in">

          {/* Header */}
          <div className="text-center mb-8">
            <img src="/logo.png" alt="Solstice Events" className="h-12 mx-auto mb-4" />
            <h1 className="text-2xl font-extrabold text-[#1E2A4A]">Welcome back</h1>
            <p className="text-gray-500 text-sm mt-1">Sign in to your account</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email" name="email" required
                value={form.email} onChange={handleChange}
                placeholder="you@example.com"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300
                  focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'} name="password" required
                  value={form.password} onChange={handleChange}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 pr-10 rounded-xl border border-gray-300
                    focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  tabIndex={-1}
                  aria-label={showPwd ? 'Hide password' : 'Show password'}
                >
                  <EyeIcon open={showPwd} />
                </button>
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-60
                text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              {loading && <Spinner size="sm" />}
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Don't have an account?{' '}
            <Link to="/register" className="text-orange-500 hover:underline font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
