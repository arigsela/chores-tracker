import axios from 'axios'
import { z } from 'zod'

// Schemas
export const LoginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

export const UserSchema = z.object({
  id: z.number(),
  username: z.string(),
  email: z.string().email(),
  full_name: z.string(),
  is_parent: z.boolean(),
  is_active: z.boolean(),
})

export type LoginData = z.infer<typeof LoginSchema>
export type User = z.infer<typeof UserSchema>

// Token management
const TOKEN_KEY = 'access_token'

export const tokenManager = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  removeToken: () => localStorage.removeItem(TOKEN_KEY),
}

// API client setup
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = tokenManager.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      tokenManager.removeToken()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth service
export const authService = {
  async login(data: LoginData) {
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)

    const response = await apiClient.post('/api/v2/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const { access_token } = response.data.data
    tokenManager.setToken(access_token)
    
    return this.getCurrentUser()
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/v2/users/me')
    return UserSchema.parse(response.data.data)
  },

  logout() {
    tokenManager.removeToken()
  },

  isAuthenticated() {
    return !!tokenManager.getToken()
  },
}

export { apiClient }