import { useState } from 'react'

export default function CommandInput({ onSubmit, loading }) {
  const [value, setValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!value.trim() || loading) return
    onSubmit(value.trim())
    setValue('')
  }

  const suggestions = [
    'Book me a haircut tomorrow afternoon',
    'Find a coffee shop near downtown Toronto',
    'Schedule a dentist appointment this week',
  ]

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className={`relative rounded-xl transition-all duration-300 ${loading ? 'glow-border' : 'border border-jarvis-border hover:border-jarvis-muted'}`}>
          <span className="absolute left-4 top-1/2 -translate-y-1/2 font-mono text-jarvis-accent text-sm select-none">&gt;_</span>
          <input
            type="text"
            value={value}
            onChange={e => setValue(e.target.value)}
            disabled={loading}
            placeholder="Give Jarvis a command..."
            className="w-full bg-jarvis-surface text-jarvis-text font-body text-sm pl-10 pr-24 py-4 rounded-xl outline-none placeholder:text-jarvis-muted disabled:opacity-50"
          />
          <button type="submit" disabled={!value.trim() || loading}
            className="absolute right-3 top-1/2 -translate-y-1/2 bg-jarvis-accent text-white text-xs font-mono px-4 py-2 rounded-lg hover:bg-jarvis-glow transition-colors disabled:opacity-30">
            {loading ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />
                running
              </span>
            ) : 'run'}
          </button>
        </div>
      </form>
      {!loading && (
        <div className="flex flex-wrap gap-2 mt-3">
          {suggestions.map(s => (
            <button key={s} onClick={() => onSubmit(s)}
              className="text-xs font-mono text-jarvis-muted border border-jarvis-border px-3 py-1.5 rounded-full hover:border-jarvis-accent hover:text-jarvis-accent transition-colors">
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
