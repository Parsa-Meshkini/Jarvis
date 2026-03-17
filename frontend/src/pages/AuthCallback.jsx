import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const setAuth  = useAuthStore(s => s.setAuth)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token  = params.get('token')
    const name   = params.get('name')
    const email  = params.get('email')

    if (token) {
      setAuth({ name, email }, token)
      const onboarded = localStorage.getItem('jarvis_onboarded')
      navigate(onboarded ? '/dashboard' : '/onboarding')
    } else {
      navigate('/login')
    }
  }, [])

  return (
    <div className="min-h-screen bg-jarvis-bg flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-jarvis-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="font-mono text-jarvis-muted text-xs">signing you in...</p>
      </div>
    </div>
  )
}
