import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export const sendCommand = async (userInput) => {
  const res = await api.post('/command', { user_input: userInput })
  return res.data
}

export const fetchTasks = async () => {
  const res = await api.get('/tasks')
  return res.data
}

export const fetchTask = async (taskId) => {
  const res = await api.get(`/tasks/${taskId}`)
  return res.data
}

export const checkHealth = async () => {
  const res = await api.get('/health')
  return res.data
}

// Poll a task until it reaches a terminal state
export const pollTask = async (taskId, onUpdate, intervalMs = 1500) => {
  const terminal = ['completed', 'failed', 'partial']

  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const task = await fetchTask(taskId)
        onUpdate(task)
        if (terminal.includes(task.status)) {
          clearInterval(interval)
          resolve(task)
        }
      } catch (err) {
        clearInterval(interval)
        reject(err)
      }
    }, intervalMs)
  })
}