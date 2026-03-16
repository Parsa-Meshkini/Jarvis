export default function StatusBadge({ status }) {
  const map = {
    completed:       { color: 'text-jarvis-green',  dot: 'bg-jarvis-green',  label: 'completed' },
    confirmed:       { color: 'text-jarvis-green',  dot: 'bg-jarvis-green',  label: 'confirmed' },
    planning:        { color: 'text-jarvis-accent', dot: 'bg-jarvis-accent', label: 'planning'  },
    executing:       { color: 'text-jarvis-amber',  dot: 'bg-jarvis-amber',  label: 'executing' },
    queued:          { color: 'text-jarvis-sub',    dot: 'bg-jarvis-muted',  label: 'queued'    },
    failed:          { color: 'text-jarvis-red',    dot: 'bg-jarvis-red',    label: 'failed'    },
    partial:         { color: 'text-jarvis-amber',  dot: 'bg-jarvis-amber',  label: 'partial'   },
    not_implemented: { color: 'text-jarvis-muted',  dot: 'bg-jarvis-dim',    label: 'skipped'   },
    pending:         { color: 'text-jarvis-sub',    dot: 'bg-jarvis-muted',  label: 'pending'   },
    running:         { color: 'text-jarvis-accent', dot: 'bg-jarvis-accent', label: 'running'   },
    success:         { color: 'text-jarvis-green',  dot: 'bg-jarvis-green',  label: 'success'   },
  }
  const s = map[status] || { color: 'text-jarvis-sub', dot: 'bg-jarvis-muted', label: status }
  return (
    <span className={`inline-flex items-center gap-1.5 font-mono text-xs ${s.color}`}>
      <span className={`status-dot ${s.dot} ${['executing','planning','running'].includes(status) ? 'animate-pulse' : ''}`} />
      {s.label}
    </span>
  )
}
