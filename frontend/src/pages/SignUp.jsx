import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { register as registerApi } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import Spinner from '../components/Spinner'

export default function SignUp() {
  const { login } = useAuth()
  const navigate  = useNavigate()

  const [form, setForm]       = useState({ email: '', password: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const { data } = await registerApi({
        email: form.email,
        password: form.password,
        role: 'customer',
      })
      login(data.access_token)
      toast.success('Account created! Welcome to Solstice Events.')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Registration failed. Please try again.'
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

          <div className="text-center mb-8">
            <img src="/logo.png" alt="Solstice Events" className="h-12 mx-auto mb-4" />
            <h1 className="text-2xl font-extrabold text-[#1E2A4A]">Create your account</h1>
            <p className="text-gray-500 text-sm mt-1">Join Solstice Events today</p>
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
              <input
                type="password" name="password" required minLength={6}
                value={form.password} onChange={handleChange}
                placeholder="Minimum 6 characters"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300
                  focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <input
                type="password" name="confirm" required
                value={form.confirm} onChange={handleChange}
                placeholder="Repeat your password"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300
                  focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
              />
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-60
                text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              {loading && <Spinner size="sm" />}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-orange-500 hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
