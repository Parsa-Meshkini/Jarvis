// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import HomePage    from './pages/HomePage'
import AuthPage    from './pages/AuthPage'
import Dashboard   from './pages/Dashboard'
import useAuthStore from './store/authStore'

function ProtectedRoute({ children }) {
  const token = useAuthStore(s => s.token)
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<HomePage />} />
        <Route path="/login"     element={<AuthPage mode="login" />} />
        <Route path="/signup"    element={<AuthPage mode="signup" />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}