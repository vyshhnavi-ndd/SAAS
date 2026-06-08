import { useState, useContext } from 'react'
import { authService } from '../services/auth'
import { AuthContext } from '../context/AuthContext'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setUser } = useContext(AuthContext)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new FormData(e.currentTarget)
      const email = formData.get('email') as string
      const password = formData.get('password') as string

      let response
      if (isSignup) {
        const tenantName = formData.get('tenantName') as string
        response = await authService.signup({
          tenant_name: tenantName,
          email,
          password,
        })
      } else {
        response = await authService.login({ email, password })
      }

      localStorage.setItem('token', response.access_token)
      localStorage.setItem(
        'user',
        JSON.stringify({
          user_id: response.user_id,
          tenant_id: response.tenant_id,
        })
      )

      setUser({
        user_id: response.user_id,
        tenant_id: response.tenant_id,
      })

      window.location.href = '/dashboard'
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>RAG SaaS</h1>
        <p>Document Q&A with AI</p>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <div className={styles.formGroup}>
              <label htmlFor="tenantName">Tenant Name</label>
              <input
                id="tenantName"
                name="tenantName"
                type="text"
                required
                placeholder="Your Company Name"
              />
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              required
              placeholder="you@example.com"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              required
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={styles.submitBtn}
          >
            {loading ? 'Loading...' : isSignup ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        <div className={styles.toggle}>
          <span>
            {isSignup ? 'Already have an account? ' : "Don't have an account? "}
            <button
              type="button"
              onClick={() => setIsSignup(!isSignup)}
              className={styles.toggleBtn}
            >
              {isSignup ? 'Sign In' : 'Sign Up'}
            </button>
          </span>
        </div>
      </div>
    </div>
  )
}
