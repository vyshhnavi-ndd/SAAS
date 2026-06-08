import { createContext } from 'react'

interface User {
  user_id: string
  tenant_id: string
}

interface AuthContextType {
  user: User | null
  setUser: (user: User | null) => void
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  setUser: () => {},
})
