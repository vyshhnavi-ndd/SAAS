import apiClient from './api'

interface SignupRequest {
  tenant_name: string
  email: string
  password: string
}

interface LoginRequest {
  email: string
  password: string
}

interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  tenant_id: string
}

export const authService = {
  signup: async (data: SignupRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/api/v1/auth/signup', data)
    return response.data
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/api/v1/auth/login', data)
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },
}
