import { useState, useEffect } from 'react'
import Header from './components/Header'
import CommandInput from './components/CommandInput'
import TaskCard from './components/TaskCard'
import TaskHistory from './components/TaskHistory'
import { sendCommand, pollTask, fetchTasks } from './api'
import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export default function App() {
  const [loading, setLoading]         = useState(false)
  const [activeTask, setActiveTask]   = useState(null)
  const [error, setError]             = useState(null)
  const [refresh, setRefresh]         = useState(0)
  const [showHistory, setShowHistory] = useState(true)
  const [tab, setTab]                 = useState('task')  // 'task' | 'memory'
  const [memory, setMemory]           = useState({})
  const [memKey, setMemKey]           = useState('')
  const [memVal, setMemVal]           = useState('')

  useEffect(() => {
    api.get('/memory').then(r => setMemory(r.data.preferences || {}))
  }, [])

  const saveMemory = async () => {
    if (!memKey.trim() || !memVal.trim()) return
    await api.post('/memory', { key: memKey, value: memVal })
    const r = await api.get('/memory')
    setMemory(r.data.preferences || {})
    setMemKey('')
    setMemVal('')
  }

  const deleteMemory = async (key) => {
    await api.delete(`/memory/${key}`)
    const r = await api.get('/memory')
    setMemory(r.data.preferences || {})
  }

  const handleCommand = async (input) => {
    setLoading(true)
    setError(null)
    setActiveTask(null)
    setTab('task')
    try {
      const result = await sendCommand(input)
      setActiveTask(result)
      if (result.status === 'queued' && result.task_id) {
        await pollTask(result.task_id, setActiveTask)
      }
      setRefresh(r => r + 1)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-jarvis-bg overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <aside className={`flex flex-col border-r border-jarvis-border transition-all duration-200 ${showHistory ? 'w-64' : 'w-0 overflow-hidden'}`}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-jarvis-border">
            <span className="font-mono text-jarvis-sub text-xs uppercase tracking-widest">history</span>
            <button onClick={() => setShowHistory(false)} className="text-jarvis-muted text-xs hover:text-jarvis-text">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <TaskHistory onSelect={(t) => { setActiveTask(t); setTab('task') }} selectedId={activeTask?.task_id} refreshTrigger={refresh} />
          </div>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden relative">
          {!showHistory && (
            <button onClick={() => setShowHistory(true)}
              className="absolute left-2 top-4 z-10 text-xs font-mono text-jarvis-muted border border-jarvis-border px-2 py-1 rounded hover:border-jarvis-accent hover:text-jarvis-accent transition-colors">
              history
            </button>
          )}

          {/* Command bar */}
          <div className="px-6 py-5 border-b border-jarvis-border">
            <CommandInput onSubmit={handleCommand} loading={loading} />
          </div>

          {/* Tabs */}
          <div className="flex border-b border-jarvis-border px-6">
            {['task', 'memory'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`font-mono text-xs py-2.5 mr-6 border-b-2 transition-colors
                  ${tab === t
                    ? 'border-jarvis-accent text-jarvis-accent'
                    : 'border-transparent text-jarvis-muted hover:text-jarvis-sub'}`}>
                {t}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">

            {/* Task tab */}
            {tab === 'task' && (
              <>
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
                         activeTask?.status === 'executing' ? 'executing...' : 'thinking...'}
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
                      {['🗓 calendar aware','📍 real location search','🤖 AI planning','💾 task history','🧠 memory'].map(f => (
                        <span key={f} className="text-xs font-mono text-jarvis-muted border border-jarvis-border px-3 py-1.5 rounded-full">{f}</span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Memory tab */}
            {tab === 'memory' && (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <p className="font-mono text-jarvis-sub text-xs mb-3">
                    Jarvis remembers these preferences and uses them in every task.
                  </p>

                  {/* Existing preferences */}
                  {Object.keys(memory).length > 0 ? (
                    <div className="space-y-2 mb-4">
                      {Object.entries(memory).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between px-4 py-3 bg-jarvis-surface border border-jarvis-border rounded-lg">
                          <div>
                            <span className="font-mono text-jarvis-accent text-xs">{key}</span>
                            <span className="text-jarvis-sub text-xs ml-3">{value}</span>
                          </div>
                          <button onClick={() => deleteMemory(key)}
                            className="text-jarvis-muted text-xs hover:text-jarvis-red transition-colors font-mono">
                            delete
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-jarvis-muted text-xs font-mono mb-4">no preferences saved yet</p>
                  )}

                  {/* Add new preference */}
                  <div className="border border-jarvis-border rounded-xl p-4 space-y-3">
                    <p className="font-mono text-jarvis-sub text-xs">add preference</p>
                    <div className="flex gap-2">
                      <input
                        value={memKey}
                        onChange={e => setMemKey(e.target.value)}
                        placeholder="key  (e.g. location)"
                        className="flex-1 bg-jarvis-bg border border-jarvis-border rounded-lg px-3 py-2 text-xs font-mono text-jarvis-text placeholder:text-jarvis-muted outline-none focus:border-jarvis-accent"
                      />
                      <input
                        value={memVal}
                        onChange={e => setMemVal(e.target.value)}
                        placeholder="value  (e.g. Toronto, ON)"
                        className="flex-1 bg-jarvis-bg border border-jarvis-border rounded-lg px-3 py-2 text-xs font-mono text-jarvis-text placeholder:text-jarvis-muted outline-none focus:border-jarvis-accent"
                      />
                      <button onClick={saveMemory}
                        className="bg-jarvis-accent text-white text-xs font-mono px-4 py-2 rounded-lg hover:bg-jarvis-glow transition-colors">
                        save
                      </button>
                    </div>

                    {/* Quick suggestions */}
                    <div className="flex flex-wrap gap-2">
                      {[
                        { key: 'location',       value: 'Toronto, ON' },
                        { key: 'preferred_time', value: 'morning' },
                        { key: 'name',           value: 'Parsa' },
                      ].map(s => (
                        <button key={s.key}
                          onClick={() => { setMemKey(s.key); setMemVal(s.value) }}
                          className="text-xs font-mono text-jarvis-muted border border-jarvis-border px-2 py-1 rounded-full hover:border-jarvis-accent hover:text-jarvis-accent transition-colors">
                          {s.key}: {s.value}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}