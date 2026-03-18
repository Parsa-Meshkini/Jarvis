import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api'
import useAuthStore from '../store/authStore'

export default function AuthPage({ mode = 'login' }) {
  const navigate  = useNavigate()
  const setAuth   = useAuthStore(s => s.setAuth)
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
      navigate(isLogin ? '/dashboard' : '/onboarding')
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
          <img src="/android-chrome-192x192.png" alt="Jarvis" className="w-10 h-10 rounded-xl object-cover" />
          <span className="font-display text-jarvis-text text-xl">Jarvis</span>
        </button>
        </div>

        {/* Card */}
        <div className="bg-jarvis-surface border border-jarvis-border rounded-2xl p-8">
          <h2 className="font-display text-2xl text-jarvis-text mb-1">
            {isLogin ? 'Welcome back' : 'Create account'}
          </h2>
          <p className="font-mono text-jarvis-sub text-xs mb-6">
            {isLogin ? 'Sign in to your Jarvis account' : 'Start automating your life'}
          </p>

          {/* Google button — outside the form */}
          <a
            href="http://localhost:8000/auth/google"
            className="flex items-center justify-center gap-3 w-full border border-jarvis-border
                       rounded-xl py-3 mb-4 hover:border-jarvis-accent/40 transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            <span className="font-mono text-jarvis-sub text-sm">continue with Google</span>
          </a>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-jarvis-border" />
            <span className="font-mono text-jarvis-muted text-xs">or</span>
            <div className="flex-1 h-px bg-jarvis-border" />
          </div>

          {/* Email/password form */}
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
                  className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3
                             text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none
                             focus:border-jarvis-accent transition-colors"
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
                className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3
                           text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none
                           focus:border-jarvis-accent transition-colors"
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
                className="w-full bg-jarvis-bg border border-jarvis-border rounded-lg px-4 py-3
                           text-sm text-jarvis-text placeholder:text-jarvis-muted outline-none
                           focus:border-jarvis-accent transition-colors"
              />
            </div>

            {error && (
              <p className="font-mono text-jarvis-red text-xs bg-jarvis-red/5
                            border border-jarvis-red/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-jarvis-accent text-white font-mono text-sm py-3 rounded-xl
                         hover:bg-jarvis-glow transition-colors disabled:opacity-50 mt-2"
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