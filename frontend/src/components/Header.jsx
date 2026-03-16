import { useEffect, useState } from 'react'
import { checkHealth } from '../api'

export default function Header() {
  const [online, setOnline] = useState(null)

  useEffect(() => {
    const check = () => checkHealth().then(() => setOnline(true)).catch(() => setOnline(false))
    check()
    const interval = setInterval(check, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-jarvis-border">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-jarvis-accent/20 border border-jarvis-accent/40 flex items-center justify-center animate-glow-pulse">
          <span className="font-mono text-jarvis-accent text-sm font-medium">J</span>
        </div>
        <div>
          <h1 className="font-display text-jarvis-text text-lg leading-none">Jarvis</h1>
          <p className="font-mono text-jarvis-muted text-xs mt-0.5">autonomous agent</p>
        </div>
      </div>
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className={`status-dot ${online === null ? 'bg-jarvis-muted' : online ? 'bg-jarvis-green animate-pulse' : 'bg-jarvis-red'}`} />
        <span className={online === null ? 'text-jarvis-muted' : online ? 'text-jarvis-green' : 'text-jarvis-red'}>
          {online === null ? 'connecting' : online ? 'api online' : 'api offline'}
        </span>
      </div>
    </header>
  )
}
