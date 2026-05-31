import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const done = useRef(false)

  useEffect(() => {
    if (done.current) return
    const params = new URLSearchParams(window.location.search)
    const err = params.get('error')
    if (err) {
      done.current = true
      navigate(`/login?error=${encodeURIComponent(err)}`, { replace: true })
      return
    }

    const token = params.get('token')
    const name = params.get('name') ?? ''
    const email = params.get('email') ?? ''
    const id = params.get('id') ?? ''
    const isNewUser = params.get('is_new_user') === '1'

    if (!token?.trim()) {
      done.current = true
      navigate('/login?error=missing_token', { replace: true })
      return
    }

    done.current = true
    setAuth(
      { id, name, email },
      token
    )
    const onboardingKey = id ? `jarvis_onboarded_${id}` : null
    const onboarded =
      (onboardingKey ? localStorage.getItem(onboardingKey) === 'true' : false) ||
      localStorage.getItem('jarvis_onboarded') === 'true'
    navigate((isNewUser || !onboarded) ? '/onboarding' : '/dashboard', { replace: true })
  }, [navigate, setAuth])

  return (
    <div className="min-h-screen bg-jarvis-bg flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-jarvis-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="font-mono text-jarvis-muted text-xs">signing you in...</p>
      </div>
    </div>
  )
}
