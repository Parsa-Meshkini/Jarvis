import { useState } from 'react'
import StatusBadge from './StatusBadge'

export default function StepRow({ step, index, delay = 0 }) {
  const [expanded, setExpanded] = useState(false)
  const output = step.output || step.result
  let parsedOutput = null
  if (output && typeof output === 'object') parsedOutput = output
  else if (typeof output === 'string') {
    try { parsedOutput = JSON.parse(output.replace(/'/g, '"')) } catch { parsedOutput = null }
  }

  return (
    <div className="animate-slide-up border border-jarvis-border rounded-lg overflow-hidden"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'both', opacity: 0 }}>
      <button onClick={() => output && setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-jarvis-dim/40 transition-colors text-left">
        <span className="font-mono text-xs text-jarvis-muted w-5 shrink-0">{String(index + 1).padStart(2, '0')}</span>
        <span className="font-mono text-sm text-jarvis-accent flex-1">{step.tool || step.name}</span>
        {step.reason && <span className="text-xs text-jarvis-sub hidden sm:block flex-1 truncate">{step.reason}</span>}
        <StatusBadge status={step.status} />
        {output && <span className={`text-jarvis-muted text-xs transition-transform ${expanded ? 'rotate-180' : ''}`}>▾</span>}
      </button>
      {expanded && output && (
        <div className="border-t border-jarvis-border bg-jarvis-bg px-4 py-3">
          {parsedOutput?.results ? (
            <div className="space-y-2">
              {parsedOutput.results.map((r, i) => (
                <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-jarvis-border/50 last:border-0">
                  <div>
                    <span className="text-jarvis-text font-medium">{r.name}</span>
                    <span className="text-jarvis-sub ml-2">{r.address}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    {r.open_now === true && <span className="text-jarvis-green">open</span>}
                    {r.rating && <span className="font-mono text-jarvis-amber">⭐ {r.rating}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <pre className="font-mono text-xs text-jarvis-sub overflow-x-auto whitespace-pre-wrap">
              {typeof output === 'string' ? output : JSON.stringify(output, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
