import { useState } from 'react'
import Header from './components/Header'
import CommandInput from './components/CommandInput'
import TaskCard from './components/TaskCard'
import TaskHistory from './components/TaskHistory'
import { sendCommand, pollTask } from './api'

export default function App() {
  const [loading, setLoading]         = useState(false)
  const [activeTask, setActiveTask]   = useState(null)
  const [error, setError]             = useState(null)
  const [refresh, setRefresh]         = useState(0)
  const [showHistory, setShowHistory] = useState(true)

  const handleCommand = async (input) => {
    setLoading(true)
    setError(null)
    setActiveTask(null)

    try {
      const result = await sendCommand(input)
      setActiveTask(result)

      // If queued (ARQ mode) — poll until complete
      if (result.status === 'queued' && result.task_id) {
        await pollTask(result.task_id, (updated) => {
          setActiveTask(updated)
        })
      }

      setRefresh(r => r + 1)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Something went wrong. Is the API running?'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-jarvis-bg overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">

        <aside className={`flex flex-col border-r border-jarvis-border transition-all duration-200
          ${showHistory ? 'w-64' : 'w-0 overflow-hidden'}`}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-jarvis-border">
            <span className="font-mono text-jarvis-sub text-xs uppercase tracking-widest">history</span>
            <button onClick={() => setShowHistory(false)} className="text-jarvis-muted text-xs hover:text-jarvis-text">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <TaskHistory onSelect={setActiveTask} selectedId={activeTask?.task_id} refreshTrigger={refresh} />
          </div>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden relative">
          {!showHistory && (
            <button onClick={() => setShowHistory(true)}
              className="absolute left-2 top-4 z-10 text-xs font-mono text-jarvis-muted border border-jarvis-border px-2 py-1 rounded hover:border-jarvis-accent hover:text-jarvis-accent transition-colors">
              history
            </button>
          )}

          <div className="px-6 py-5 border-b border-jarvis-border">
            <CommandInput onSubmit={handleCommand} loading={loading} />
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            {loading && (
              <div className="flex flex-col items-center justify-center py-16 gap-4 animate-fade-in">
                <div className="relative w-12 h-12">
                  <div className="absolute inset-0 border-2 border-jarvis-accent/20 rounded-full" />
                  <div className="absolute inset-0 border-2 border-jarvis-accent border-t-transparent rounded-full animate-spin" />
                </div>
                <div className="text-center">
                  <p className="font-mono text-jarvis-accent text-sm">
                    {activeTask?.status === 'queued'    ? 'queued...'    :
                     activeTask?.status === 'planning'  ? 'planning...'  :
                     activeTask?.status === 'executing' ? 'executing...' :
                     'thinking...'}
                  </p>
                  <p className="font-mono text-jarvis-muted text-xs mt-1">Jarvis is working on it</p>
                </div>
              </div>
            )}

            {error && !loading && (
              <div className="border border-jarvis-red/30 bg-jarvis-red/5 rounded-xl p-4 animate-fade-in">
                <p className="font-mono text-jarvis-red text-sm">error</p>
                <p className="text-jarvis-sub text-xs mt-1">{error}</p>
              </div>
            )}

            {activeTask && !loading && <TaskCard task={activeTask} isLatest={true} />}

            {!activeTask && !loading && !error && (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <div className="w-16 h-16 rounded-2xl bg-jarvis-surface border border-jarvis-border flex items-center justify-center">
                  <span className="font-display text-jarvis-accent text-2xl">J</span>
                </div>
                <p className="font-display text-jarvis-text text-xl">Ready</p>
                <p className="font-mono text-jarvis-muted text-xs">Give Jarvis a command above</p>
                <div className="flex flex-wrap gap-2 mt-4 justify-center max-w-md">
                  {['🗓 calendar aware','📍 real location search','🤖 AI planning','💾 task history'].map(f => (
                    <span key={f} className="text-xs font-mono text-jarvis-muted border border-jarvis-border px-3 py-1.5 rounded-full">{f}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}