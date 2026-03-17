import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user:  JSON.parse(localStorage.getItem('jarvis_user') || 'null'),
  token: localStorage.getItem('jarvis_token') || null,

  setAuth: (user, token) => {
    localStorage.setItem('jarvis_user',  JSON.stringify(user))
    localStorage.setItem('jarvis_token', token)
    set({ user, token })
  },

  logout: () => {
    localStorage.removeItem('jarvis_user')
    localStorage.removeItem('jarvis_token')
    set({ user: null, token: null })
  },
}))

export default useAuthStore