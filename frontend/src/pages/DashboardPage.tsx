import { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'
import { authService } from '../services/auth'
import { documentService } from '../services/documents'
import styles from './DashboardPage.module.css'

interface Document {
  id: string
  original_filename: string
  document_size_bytes: number
  processed: boolean
  upload_date: string
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user, setUser } = useContext(AuthContext)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const docs = await documentService.list()
      setDocuments(docs)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    authService.logout()
    setUser(null)
    navigate('/')
  }

  const handleUploadClick = () => {
    navigate('/dashboard/upload')
  }

  const handleChatClick = () => {
    navigate('/chat')
  }

  const handleDeleteDocument = async (docId: string) => {
    if (!window.confirm('Delete this document? This will remove it from search.')) {
      return
    }

    try {
      await documentService.delete(docId)
      setDocuments(documents.filter((d) => d.id !== docId))
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1>Dashboard</h1>
          <p className={styles.subtitle}>Document Q&A with AI</p>
        </div>
        <button onClick={handleLogout} className={styles.logoutBtn}>
          Logout
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.actionsGrid}>
        <div className={styles.actionCard}>
          <div className={styles.icon}>📤</div>
          <h3>Upload Documents</h3>
          <p>Upload PDF, DOCX, or TXT files</p>
          <button onClick={handleUploadClick} className={styles.primaryBtn}>
            Upload Now
          </button>
        </div>

        <div className={styles.actionCard}>
          <div className={styles.icon}>💬</div>
          <h3>Start Chat</h3>
          <p>Ask questions about your documents</p>
          <button onClick={handleChatClick} className={styles.primaryBtn}>
            Go to Chat
          </button>
        </div>

        <div className={styles.actionCard}>
          <div className={styles.icon}>📊</div>
          <h3>Statistics</h3>
          <p>
            {documents.length} document{documents.length !== 1 ? 's' : ''} uploaded
          </p>
          <div className={styles.stat}>
            {documents.filter((d) => d.processed).length} processed
          </div>
        </div>
      </div>

      <div className={styles.documentsSection}>
        <h2>Your Documents</h2>

        {loading ? (
          <div className={styles.loading}>Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className={styles.empty}>
            <p>No documents uploaded yet.</p>
            <button onClick={handleUploadClick} className={styles.primaryBtn}>
              Upload your first document
            </button>
          </div>
        ) : (
          <div className={styles.documentsList}>
            {documents.map((doc) => (
              <div key={doc.id} className={styles.documentItem}>
                <div className={styles.docInfo}>
                  <h4>{doc.original_filename}</h4>
                  <p className={styles.docMeta}>
                    {(doc.document_size_bytes / 1024).toFixed(2)} KB •{' '}
                    {new Date(doc.upload_date).toLocaleDateString()}
                  </p>
                  {doc.processed ? (
                    <span className={styles.badge}>✓ Ready for chat</span>
                  ) : (
                    <span className={styles.badgeProcessing}>
                      ⏳ Processing...
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id)}
                  className={styles.deleteBtn}
                  title="Delete document"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {user && (
        <div className={styles.userInfo}>
          <p>
            <strong>Tenant ID:</strong> {user.tenant_id}
          </p>
          <p>
            <strong>User ID:</strong> {user.user_id}
          </p>
        </div>
      )}
    </div>
  )
}

