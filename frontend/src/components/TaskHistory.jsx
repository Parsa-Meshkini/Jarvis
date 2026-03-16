import { useEffect, useState } from 'react'
import { fetchTasks } from '../api'
import StatusBadge from './StatusBadge'

export default function TaskHistory({ onSelect, selectedId, refreshTrigger }) {
  const [tasks, setTasks]     = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTasks().then(setTasks).catch(console.error).finally(() => setLoading(false))
  }, [refreshTrigger])

  if (loading) return (
    <div className="space-y-2 p-4">
      {[...Array(3)].map((_, i) => <div key={i} className="h-14 bg-jarvis-dim/40 rounded-lg animate-pulse" />)}
    </div>
  )

  if (!tasks.length) return (
    <div className="p-4 text-center">
      <p className="text-jarvis-muted text-xs font-mono">no tasks yet</p>
    </div>
  )

  return (
    <div className="space-y-1 p-2">
      {tasks.map(task => (
        <button key={task.task_id} onClick={() => onSelect(task)}
          className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors
            ${task.task_id === selectedId ? 'bg-jarvis-accent/10 border border-jarvis-accent/30' : 'hover:bg-jarvis-dim/40 border border-transparent'}`}>
          <p className="text-jarvis-text text-xs truncate font-medium">{task.request || task.user_request}</p>
          <div className="flex items-center justify-between mt-1">
            <StatusBadge status={task.status || 'unknown'} />
            {task.created_at && (
              <span className="text-jarvis-muted text-xs font-mono">
                {new Date(task.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
