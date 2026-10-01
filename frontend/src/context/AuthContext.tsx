/**
 * Authentication context and session state provider.
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  getCurrentUser,
  getStoredToken,
  loginUser,
  registerUser,
  removeStoredToken,
  setStoredToken,
} from '../services/auth'
import { User, UserLoginRequest, UserRegisterRequest } from '../types/auth'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: UserLoginRequest) => Promise<void>
  register: (credentials: UserRegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(getStoredToken())
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const refreshUser = async () => {
    const currentToken = token || getStoredToken()
    if (!currentToken) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const userData = await getCurrentUser(currentToken)
      setUser(userData)
    } catch {
      // Invalid/expired token
      removeStoredToken()
      setToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refreshUser()
  }, [token])

  const login = async (credentials: UserLoginRequest) => {
    setIsLoading(true)
    try {
      const tokenRes = await loginUser(credentials)
      setStoredToken(tokenRes.access_token)
      setToken(tokenRes.access_token)
      const userData = await getCurrentUser(tokenRes.access_token)
      setUser(userData)
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (credentials: UserRegisterRequest) => {
    setIsLoading(true)
    try {
      await registerUser(credentials)
      // Automatically log in after registration
      await login(credentials)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    removeStoredToken()
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
