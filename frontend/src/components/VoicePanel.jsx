// src/components/VoicePanel.jsx
import { useEffect, useState, useCallback } from 'react'
import { fetchActiveVoiceCalls, fetchVoiceStatus } from '../api'

export default function VoicePanel() {
  const [calls, setCalls] = useState([])
  const [selected, setSelected] = useState(null)
  const [hideTranscript, setHideTranscript] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [callMeta, setCallMeta] = useState(null)
  const [loading, setLoading] = useState(false)

  const sidForTranscript =
    hideTranscript ? null : (selected ?? calls[0]?.call_sid ?? null)

  const loadCalls = useCallback(async () => {
    try {
      const data = await fetchActiveVoiceCalls()
      setCalls(data.active_calls || [])
    } catch {
      /* keep previous */
    }
  }, [])

  // Active call list — poll frequently so new calls appear quickly
  useEffect(() => {
    loadCalls()
    const interval = setInterval(loadCalls, 2000)
    return () => clearInterval(interval)
  }, [loadCalls])

  // Reset hide when the set of calls changes (new call / ended)
  const callSig = calls.map((c) => c.call_sid).join('|')
  useEffect(() => {
    setHideTranscript(false)
  }, [callSig])

  // Transcript for selected (or first) call
  useEffect(() => {
    if (!sidForTranscript) {
      setTranscript([])
      setCallMeta(null)
      setLoading(false)
      return
    }

    let cancelled = false
    const poll = async () => {
      setLoading(true)
      try {
        const data = await fetchVoiceStatus(sidForTranscript)
        if (cancelled) return
        setTranscript(data.transcript || [])
        setCallMeta({
          type: data.type,
          business: data.business,
          active: data.active,
        })
      } catch {
        if (!cancelled) setTranscript([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    poll()
    const interval = setInterval(poll, 1200)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [sidForTranscript])

  const selectCall = (callSid) => {
    setSelected(callSid)
    setHideTranscript(false)
  }

  if (!calls.length && !sidForTranscript) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="w-14 h-14 rounded-2xl bg-jarvis-surface border border-jarvis-border flex items-center justify-center">
          <span className="text-2xl">📞</span>
        </div>
        <p className="font-mono text-jarvis-muted text-xs">No active voice calls</p>
        <p className="font-mono text-jarvis-muted text-xs opacity-60 text-center max-w-sm">
          When Jarvis calls a business (or receives a call), the live transcript appears here
        </p>
      </div>
    )
  }

  const title =
    callMeta?.type === 'outbound' && callMeta?.business
      ? `Jarvis ↔ ${callMeta.business}`
      : 'Live transcript'

  return (
    <div className="space-y-4 animate-fade-in">
      {calls.length > 0 && (
        <div className="space-y-2">
          <p className="font-mono text-jarvis-sub text-xs uppercase tracking-widest mb-3">
            active calls
          </p>
          {calls.map((call) => (
            <button
              key={call.call_sid}
              onClick={() => selectCall(call.call_sid)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-colors
                ${sidForTranscript === call.call_sid
                  ? 'border-jarvis-accent/40 bg-jarvis-accent/5'
                  : 'border-jarvis-border bg-jarvis-surface hover:border-jarvis-accent/30'}`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2 h-2 rounded-full bg-jarvis-green animate-pulse shrink-0" />
                  <span className="font-mono text-jarvis-text text-xs truncate">
                    {call.type === 'outbound' && call.business
                      ? call.business
                      : `${call.call_sid.slice(0, 12)}…`}
                  </span>
                </div>
                <span className="font-mono text-jarvis-muted text-xs shrink-0">
                  {call.turns} turns
                </span>
              </div>
              {call.last_message && (
                <p className="text-jarvis-sub text-xs mt-1.5 truncate">{call.last_message}</p>
              )}
              {call.type === 'outbound' && (
                <p className="font-mono text-jarvis-muted text-[10px] mt-1">outbound</p>
              )}
            </button>
          ))}
        </div>
      )}

      {sidForTranscript && (
        <div className="border border-jarvis-border rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-jarvis-border bg-jarvis-surface">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2 h-2 rounded-full bg-jarvis-green animate-pulse shrink-0" />
              <span className="font-mono text-jarvis-text text-xs truncate">{title}</span>
            </div>
            <button
              type="button"
              onClick={() => {
                setHideTranscript(true)
                setSelected(null)
              }}
              className="font-mono text-jarvis-muted text-xs hover:text-jarvis-text shrink-0"
            >
              hide
            </button>
          </div>

          <div className="p-4 space-y-3 max-h-96 overflow-y-auto min-h-[120px]">
            {loading && transcript.length === 0 && (
              <p className="font-mono text-jarvis-muted text-xs">Loading transcript…</p>
            )}
            {!loading && transcript.length === 0 && (
              <p className="font-mono text-jarvis-muted text-xs">
                Waiting for audio — Jarvis or the business will speak first.
              </p>
            )}
            {transcript.map((msg, i) => {
              const isJarvis = msg.role === 'assistant'
              return (
                <div
                  key={`${i}-${msg.content?.slice(0, 20)}`}
                  className={`flex gap-3 animate-slide-up ${isJarvis ? '' : 'flex-row-reverse'}`}
                  style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'both', opacity: 0 }}
                >
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-mono shrink-0
                    ${isJarvis ? 'bg-jarvis-accent/20 text-jarvis-accent' : 'bg-jarvis-dim text-jarvis-sub'}`}
                    title={isJarvis ? 'Jarvis' : 'Business / person on the line'}
                  >
                    {isJarvis ? 'J' : 'B'}
                  </div>
                  <div
                    className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed
                    ${isJarvis
                      ? 'bg-jarvis-surface border border-jarvis-border text-jarvis-text'
                      : 'bg-jarvis-accent/10 border border-jarvis-accent/20 text-jarvis-text'}`}
                  >
                    <span className="font-mono text-[10px] text-jarvis-muted block mb-0.5">
                      {isJarvis ? 'Jarvis' : 'Business'}
                    </span>
                    {msg.content}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {hideTranscript && calls.length > 0 && (
        <p className="font-mono text-jarvis-muted text-xs">
          Transcript hidden — tap a call above to show it again.
        </p>
      )}
    </div>
  )
}
