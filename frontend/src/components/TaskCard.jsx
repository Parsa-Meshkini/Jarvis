import { useState } from 'react'
import StatusBadge from './StatusBadge'
import StepRow from './StepRow'

export default function TaskCard({ task, isLatest = false }) {
  const [open, setOpen] = useState(isLatest)
  const steps  = task.execution?.results || task.steps || []
  const status = task.execution?.status  || task.status || 'unknown'

  return (
    <div className={`rounded-xl border transition-all duration-200 animate-fade-in
      ${isLatest ? 'border-jarvis-accent/40 bg-jarvis-surface' : 'border-jarvis-border bg-jarvis-surface/60'}`}>
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-4 p-4 text-left hover:bg-jarvis-dim/20 transition-colors rounded-xl">
        <div className={`mt-0.5 w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-sm
          ${status === 'completed' ? 'bg-jarvis-green/10 text-jarvis-green' :
            status === 'failed'    ? 'bg-jarvis-red/10 text-jarvis-red' :
                                     'bg-jarvis-accent/10 text-jarvis-accent'}`}>
          {status === 'completed' ? '✓' : status === 'failed' ? '✗' : '◌'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-jarvis-text text-sm font-medium truncate">{task.request || task.user_request}</p>
          <div className="flex items-center gap-3 mt-1.5">
            <StatusBadge status={status} />
            <span className="text-jarvis-muted text-xs font-mono">{steps.length} step{steps.length !== 1 ? 's' : ''}</span>
            {task.task_id && <span className="text-jarvis-muted text-xs font-mono hidden sm:block">{task.task_id.slice(0, 8)}...</span>}
            {task.created_at && (
              <span className="text-jarvis-muted text-xs font-mono ml-auto">
                {new Date(task.created_at).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        <span className={`text-jarvis-muted text-xs mt-1 transition-transform ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {open && steps.length > 0 && (
        <div className="px-4 pb-4 space-y-2 border-t border-jarvis-border/50 pt-3">
          {steps.map((step, i) => <StepRow key={i} step={step} index={i} delay={i * 60} />)}
        </div>
      )}
    </div>
  )
}
