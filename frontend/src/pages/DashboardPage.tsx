import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'
import { authService } from '../services/auth'

export default function DashboardPage() {
  const { user, setUser } = useContext(AuthContext)

  const handleLogout = () => {
    authService.logout()
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>Dashboard</h1>
        <button onClick={handleLogout} style={{ background: '#dc3545', color: 'white' }}>
          Logout
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
        <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3>📤 Upload Documents</h3>
          <p>Upload PDF, DOCX, or TXT files to start</p>
          <button style={{ marginTop: '10px', background: '#007bff', color: 'white', width: '100%' }}>
            Upload Now
          </button>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3>💬 Start Chat</h3>
          <p>Ask questions about your documents</p>
          <button style={{ marginTop: '10px', background: '#28a745', color: 'white', width: '100%' }}>
            Go to Chat
          </button>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3>📚 My Documents</h3>
          <p>View and manage your uploaded files</p>
          <button style={{ marginTop: '10px', background: '#17a2b8', color: 'white', width: '100%' }}>
            View Documents
          </button>
        </div>
      </div>

      {user && (
        <div style={{ marginTop: '30px', padding: '15px', background: '#e7f3ff', borderRadius: '4px', fontSize: '12px' }}>
          <p><strong>User ID:</strong> {user.user_id}</p>
          <p><strong>Tenant ID:</strong> {user.tenant_id}</p>
        </div>
      )}
    </div>
  )
}
