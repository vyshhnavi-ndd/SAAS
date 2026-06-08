import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import { AuthContext } from './context/AuthContext'

interface User {
  user_id: string
  tenant_id: string
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')

    if (token && userData) {
      setUser(JSON.parse(userData))
    }

    setLoading(false)
  }, [])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      <BrowserRouter>
        <Routes>
          {!user ? (
            <Route path="*" element={<LoginPage />} />
          ) : (
            <>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </>
          )}
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}

export default App
