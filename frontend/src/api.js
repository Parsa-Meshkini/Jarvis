import axios from 'axios'

const BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('jarvis_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const register = async (name, email, password) => {
  const res = await api.post('/auth/register', { name, email, password })
  return res.data
}

export const login = async (email, password) => {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

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

export const fetchMemory = async () => {
  const res = await api.get('/memory')
  return res.data
}

export const saveMemory = async (key, value) => {
  const res = await api.post('/memory', { key, value })
  return res.data
}

export const deleteMemory = async (key) => {
  const res = await api.delete(`/memory/${key}`)
  return res.data
}

export const fetchActiveVoiceCalls = async () => {
  const res = await api.get('/voice/active')
  return res.data
}

export const fetchVoiceStatus = async (callSid) => {
  const res = await api.get(`/voice/status/${callSid}`)
  return res.data
}

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