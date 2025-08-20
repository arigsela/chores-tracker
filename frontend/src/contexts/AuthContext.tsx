import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI } from '@/api/client';

interface User {
  id: number;
  username: string;
  role: 'parent' | 'child';
  email?: string;
  full_name?: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const USER_KEY = '@chores_tracker:user';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setIsLoading(true);
      const token = await authAPI.getToken();
      
      if (token) {
        // Try to get fresh user data from the API
        try {
          const userResponse = await authAPI.getCurrentUser();
          const userData: User = {
            id: userResponse.id,
            username: userResponse.username,
            role: userResponse.is_parent ? 'parent' : 'child',
            email: userResponse.email || undefined,
            full_name: userResponse.full_name || undefined,
          };
          await AsyncStorage.setItem(USER_KEY, JSON.stringify(userData));
          setUser(userData);
          setIsAuthenticated(true);
        } catch (apiError) {
          // If API call fails, try to use stored user data
          const storedUser = await AsyncStorage.getItem(USER_KEY);
          if (storedUser) {
            setUser(JSON.parse(storedUser));
            setIsAuthenticated(true);
          } else {
            // No stored user data and API failed, log out
            setIsAuthenticated(false);
            setUser(null);
            await authAPI.logout();
          }
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await authAPI.login(username, password);
      
      // Extract user data from the response
      const userData: User = {
        id: response.user.id,
        username: response.user.username,
        role: response.user.is_parent ? 'parent' : 'child',
        email: response.user.email || undefined,
        full_name: response.user.full_name || undefined,
      };
      
      await AsyncStorage.setItem(USER_KEY, JSON.stringify(userData));
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('AuthContext: Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local state regardless of API success/failure
      try {
        await AsyncStorage.removeItem(USER_KEY);
      } catch (storageError) {
        console.error('Storage cleanup error:', storageError);
      }
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
        checkAuthStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};