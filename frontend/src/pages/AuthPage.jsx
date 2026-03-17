// src/pages/AuthPage.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api'
import useAuthStore from '../store/authStore'

export default function AuthPage({ mode = 'login' }) {
  const navigate    = useNavigate()
  const setAuth     = useAuthStore(s => s.setAuth)
  const [isLogin, setIsLogin] = useState(mode === 'login')
  const [form, setForm]       = useState({ name: '', email: '', password: '' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const data = isLogin
        ? await login(form.email, form.password)
        : await register(form.name, form.email, form.password)

      setAuth(data.user, data.token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-jarvis-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <button onClick={() => navigate('/')} className="inline-flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-10 h-10 rounded-xl bg-jarvis-accent/20 border border-jarvis-accent/40 flex items-center justify-center animate-glow-pulse">
              <span className="font-mono text-jarvis-accent">J</span>
            </div>
            <span className="font-display text-jarvis-text text-xl">Jarvis</span>
          </button>
        </div>

        {/* Card */}
        <div className="bg-jarvis-surface border border-jarvis-border rounded-2xl p-8">
          <h2 className="font-display text-2xl text-jarvis-text mb-1">
            {isLogin ? 'Welcome back' : 'Create account'}
          </h2>
          <p className="text-jarvis-sub text-xs font-mono mb-6">
            {isLogin ? 'Sign in to your Jarvis account' : 'Start automating your life'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="font-mono text-jarvis-sub text-xs mb-1.5 block">name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Your name"
                  required
                  className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3 text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none focus:border-jarvis-accent transition-colors"
                />
              </div>
            )}

            <div>
              <label className="font-mono text-jarvis-sub text-xs mb-1.5 block">email</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                required
                className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3 text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none focus:border-jarvis-accent transition-colors"
              />
            </div>

            <div>
              <label className="font-mono text-jarvis-sub text-xs mb-1.5 block">password</label>
              <input
                type="password"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                required
                className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3 text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none focus:border-jarvis-accent transition-colors"
              />
            </div>

            {error && (
              <p className="font-mono text-jarvis-red text-xs bg-jarvis-red/5 border border-jarvis-red/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-jarvis-accent text-white font-mono text-sm py-3 rounded-xl hover:bg-jarvis-glow transition-colors disabled:opacity-50 mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-3.5 h-3.5 border border-white/30 border-t-white rounded-full animate-spin" />
                  {isLogin ? 'signing in...' : 'creating account...'}
                </span>
              ) : (
                isLogin ? 'sign in' : 'create account'
              )}
            </button>
          </form>

          <p className="text-center font-mono text-jarvis-muted text-xs mt-6">
            {isLogin ? "Don't have an account?" : 'Already have an account?'}
            {' '}
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-jarvis-accent hover:underline"
            >
              {isLogin ? 'sign up' : 'sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}