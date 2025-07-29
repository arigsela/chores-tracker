/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useReducer, useEffect } from 'react'
import { authService, User } from '@/services/auth.service'
import { useNavigate } from 'react-router-dom'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: User }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean }

const initialState: AuthState = {
  user: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
}

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true, error: null }
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      }
    case 'LOGOUT':
      return { ...initialState, isLoading: false }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    default:
      return state
  }
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)
  const navigate = useNavigate()

  const checkAuth = async () => {
    if (!authService.isAuthenticated()) {
      dispatch({ type: 'SET_LOADING', payload: false })
      return
    }

    try {
      const user = await authService.getCurrentUser()
      dispatch({ type: 'LOGIN_SUCCESS', payload: user })
    } catch {
      dispatch({ type: 'LOGOUT' })
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (username: string, password: string) => {
    dispatch({ type: 'LOGIN_START' })
    try {
      const user = await authService.login({ username, password })
      dispatch({ type: 'LOGIN_SUCCESS', payload: user })
      navigate('/')
    } catch (error) {
      const message = error instanceof Error && 'response' in error 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Login failed'
        : 'Login failed'
      dispatch({ type: 'LOGIN_FAILURE', payload: message })
      throw error
    }
  }

  const logout = () => {
    authService.logout()
    dispatch({ type: 'LOGOUT' })
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}