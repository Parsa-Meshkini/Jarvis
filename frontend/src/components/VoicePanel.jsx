// src/components/VoicePanel.jsx
import { useEffect, useState } from 'react'
import { fetchActiveVoiceCalls, fetchVoiceStatus } from '../api'
import StatusBadge from './StatusBadge'

export default function VoicePanel() {
  const [calls, setCalls]       = useState([])
  const [selected, setSelected] = useState(null)
  const [transcript, setTranscript] = useState([])

  // Poll for active calls every 3 seconds
  useEffect(() => {
    const poll = async () => {
      try {
        const data = await fetchActiveVoiceCalls()
        setCalls(data.active_calls || [])
      } catch { /* silent */ }
    }
    poll()
    const interval = setInterval(poll, 3000)
    return () => clearInterval(interval)
  }, [])

  // Poll transcript for selected call
  useEffect(() => {
    if (!selected) return
    const poll = async () => {
      try {
        const data = await fetchVoiceStatus(selected)
        setTranscript(data.transcript || [])
      } catch { /* silent */ }
    }
    poll()
    const interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [selected])

  if (!calls.length && !selected) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="w-14 h-14 rounded-2xl bg-jarvis-surface border border-jarvis-border flex items-center justify-center">
          <span className="text-2xl">📞</span>
        </div>
        <p className="font-mono text-jarvis-muted text-xs">No active voice calls</p>
        <p className="font-mono text-jarvis-muted text-xs opacity-60">
          Ask Jarvis to call a business to see the live transcript here
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Active calls list */}
      {calls.length > 0 && (
        <div className="space-y-2">
          <p className="font-mono text-jarvis-sub text-xs uppercase tracking-widest mb-3">
            active calls
          </p>
          {calls.map(call => (
            <button
              key={call.call_sid}
              onClick={() => setSelected(call.call_sid)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-colors
                ${selected === call.call_sid
                  ? 'border-jarvis-accent/40 bg-jarvis-accent/5'
                  : 'border-jarvis-border bg-jarvis-surface hover:border-jarvis-accent/30'}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-jarvis-green animate-pulse" />
                  <span className="font-mono text-jarvis-text text-xs">{call.call_sid.slice(0, 16)}...</span>
                </div>
                <span className="font-mono text-jarvis-muted text-xs">{call.turns} turns</span>
              </div>
              {call.last_message && (
                <p className="text-jarvis-sub text-xs mt-1.5 truncate">{call.last_message}</p>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Live transcript */}
      {selected && transcript.length > 0 && (
        <div className="border border-jarvis-border rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-jarvis-border bg-jarvis-surface">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-jarvis-green animate-pulse" />
              <span className="font-mono text-jarvis-text text-xs">live transcript</span>
            </div>
            <button
              onClick={() => { setSelected(null); setTranscript([]) }}
              className="font-mono text-jarvis-muted text-xs hover:text-jarvis-text"
            >
              close
            </button>
          </div>

          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {transcript.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 animate-slide-up ${msg.role === 'assistant' ? '' : 'flex-row-reverse'}`}
                style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both', opacity: 0 }}
              >
                {/* Avatar */}
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs shrink-0
                  ${msg.role === 'assistant'
                    ? 'bg-jarvis-accent/20 text-jarvis-accent'
                    : 'bg-jarvis-dim text-jarvis-sub'}`}>
                  {msg.role === 'assistant' ? 'J' : 'U'}
                </div>

                {/* Bubble */}
                <div className={`max-w-xs px-3 py-2 rounded-xl text-xs leading-relaxed
                  ${msg.role === 'assistant'
                    ? 'bg-jarvis-surface border border-jarvis-border text-jarvis-text'
                    : 'bg-jarvis-accent/10 border border-jarvis-accent/20 text-jarvis-text'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}