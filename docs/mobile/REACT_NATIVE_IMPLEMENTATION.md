# React Native Implementation Guide

## Overview

This guide provides a comprehensive look at the Chores Tracker React Native implementation, covering project structure, shared code patterns, API integration, navigation, state management, and deployment strategies.

### Key Architecture Decisions

- **Expo Framework**: Managed workflow with EAS Build
- **TypeScript**: Strict typing throughout the codebase
- **Context API**: Lightweight state management for auth and global state
- **React Navigation**: Type-safe navigation with stack and tab navigators
- **Axios**: HTTP client with interceptors for authentication
- **AsyncStorage**: Persistent storage for offline support

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Shared Code with Web](#shared-code-with-web)
3. [Navigation Architecture](#navigation-architecture)
4. [API Integration](#api-integration)
5. [Authentication Flow](#authentication-flow)
6. [State Management](#state-management)
7. [Offline Support](#offline-support)
8. [Component Library](#component-library)
9. [Styling Patterns](#styling-patterns)
10. [Building and Deployment](#building-and-deployment)
11. [Common Patterns](#common-patterns)

---

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx                  # Root component with AuthProvider
│   ├── api/                     # API client and endpoints
│   │   ├── client.ts            # Axios instance with auth interceptors
│   │   ├── chores.ts            # Chore-related API calls
│   │   ├── users.ts             # User-related API calls
│   │   └── __tests__/           # API unit tests
│   ├── components/              # Reusable components
│   │   ├── ChoreCard.tsx        # Chore display card
│   │   ├── ChildCard.tsx        # Child user card
│   │   ├── ActivityFeed.tsx     # Activity timeline
│   │   └── __tests__/           # Component tests
│   ├── contexts/                # React Context providers
│   │   ├── AuthContext.tsx      # Authentication state
│   │   └── __tests__/           # Context tests
│   ├── navigation/              # Navigation configuration
│   │   ├── SimpleNavigator.tsx  # Main navigation logic
│   │   ├── types.ts             # Navigation type definitions
│   │   └── __tests__/           # Navigation tests
│   ├── screens/                 # Full-screen views
│   │   ├── LoginScreen.tsx      # Login form
│   │   ├── ChoresScreen.tsx     # Chore list for children
│   │   ├── ApprovalsScreen.tsx  # Parent approval queue
│   │   ├── BalanceScreen.tsx    # Child balance view
│   │   └── __tests__/           # Screen tests
│   ├── config/                  # Configuration
│   │   └── api.ts               # API URL configuration
│   ├── utils/                   # Utility functions
│   └── test-utils/              # Testing utilities
├── assets/                      # Images, icons, fonts
│   ├── icon.png                 # App icon
│   ├── splash-icon.png          # Splash screen
│   └── adaptive-icon.png        # Android adaptive icon
├── app.json                     # Expo configuration
├── package.json                 # Dependencies and scripts
├── tsconfig.json                # TypeScript configuration
├── jest.config.js               # Jest testing configuration
├── .env                         # Environment variables (local)
├── .env.example                 # Environment variables template
└── index.ts                     # Entry point
```

---

## Shared Code with Web

### Code Sharing Strategy

**90% Code Sharing** between mobile and web:

**Shared** (90%):
- ✅ Business logic (API calls, data processing)
- ✅ State management (Context API)
- ✅ Components (UI elements)
- ✅ Screens (main views)
- ✅ Navigation logic
- ✅ Utilities and helpers
- ✅ Type definitions

**Platform-Specific** (10%):
- ❌ Storage implementation (AsyncStorage vs localStorage)
- ❌ Navigation rendering (native vs web)
- ❌ Platform-specific APIs
- ❌ Deployment configuration

### React Native Web Compatibility

All components use **React Native primitives** that work across platforms:

```typescript
// ✅ Cross-platform (works on mobile and web)
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

// ❌ Web-only (doesn't work on mobile)
import { div, button } from 'react-native-web';  // Don't use
```

### Entry Point Abstraction

**`index.ts`** (Platform-agnostic):
```typescript
import { registerRootComponent } from 'expo';
import App from './src/App';

// Works for web, iOS, and Android
registerRootComponent(App);
```

### Storage Abstraction

**Mobile**: Uses `AsyncStorage`
```typescript
// frontend/src/api/client.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = '@chores_tracker:token';

// Store token
await AsyncStorage.setItem(TOKEN_KEY, token);

// Retrieve token
const token = await AsyncStorage.getItem(TOKEN_KEY);

// Remove token
await AsyncStorage.removeItem(TOKEN_KEY);
```

**Web**: AsyncStorage polyfills to localStorage automatically via Expo

### API URL Configuration

**Dynamic URL Resolution** (`config/api.ts`):

```typescript
declare global {
  interface Window {
    APP_CONFIG?: {
      API_URL?: string;
      NODE_ENV?: string;
    };
  }
}

export const getAPIUrl = (): string => {
  // Priority 1: Runtime configuration (web nginx container)
  if (typeof window !== 'undefined' && window.APP_CONFIG?.API_URL) {
    return window.APP_CONFIG.API_URL;
  }

  // Priority 2: Build-time environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // Priority 3: Default for local development
  return 'http://localhost:8000/api/v1';
};
```

**Platform-Specific Defaults**:
```typescript
import { Platform } from 'react-native';

const getDefaultAPIUrl = () => {
  if (Platform.OS === 'android') {
    // Android emulator uses 10.0.2.2 for host machine
    return 'http://10.0.2.2:8000/api/v1';
  }
  if (Platform.OS === 'ios') {
    // iOS simulator can use localhost
    return 'http://localhost:8000/api/v1';
  }
  // Web
  return 'http://localhost:8000/api/v1';
};
```

---

## Navigation Architecture

### Simple Navigator Pattern

The app uses a **custom tab navigator** implementation for simplicity:

**`navigation/SimpleNavigator.tsx`**:

```typescript
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';

type TabName = 'Home' | 'Chores' | 'Children' | 'Approvals' | 'Balance' | 'Profile';
type AuthScreen = 'login' | 'register';

export const SimpleNavigator: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabName>('Home');
  const [authScreen, setAuthScreen] = useState<AuthScreen>('login');

  // Show auth screens if not authenticated
  if (!isAuthenticated) {
    if (authScreen === 'register') {
      return <RegisterScreen onBackToLogin={() => setAuthScreen('login')} />;
    }
    return <LoginScreen onNavigateToRegister={() => setAuthScreen('register')} />;
  }

  const isParent = user?.role === 'parent';

  const renderScreen = () => {
    switch (activeTab) {
      case 'Home':
        return <HomeScreen onNavigate={setActiveTab} />;
      case 'Chores':
        return <ChoresScreen />;
      case 'Children':
        return isParent ? <ChildrenScreen /> : <BalanceScreen />;
      // ... other cases
      default:
        return <HomeScreen onNavigate={setActiveTab} />;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Chores Tracker</Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {renderScreen()}
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'Home' && styles.activeTab]}
          onPress={() => setActiveTab('Home')}
        >
          <Text style={styles.tabIcon}>🏠</Text>
          <Text style={styles.tabLabel}>Home</Text>
        </TouchableOpacity>
        {/* ... other tabs */}
      </View>
    </View>
  );
};
```

### Navigation Type Safety

**`navigation/types.ts`**:
```typescript
export type TabName =
  | 'Home'
  | 'Chores'
  | 'Children'
  | 'Approvals'
  | 'Balance'
  | 'Profile'
  | 'Reports'
  | 'Statistics'
  | 'FamilySettings';

export type AuthScreen = 'login' | 'register';

export interface NavigationProps {
  onNavigate: (tab: TabName) => void;
}
```

### Screen Props Pattern

Screens receive navigation callback:

```typescript
interface HomeScreenProps {
  onNavigate: (tab: TabName) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  return (
    <View>
      <TouchableOpacity onPress={() => onNavigate('Chores')}>
        <Text>View Chores</Text>
      </TouchableOpacity>
    </View>
  );
};
```

### Alternative: React Navigation

For more complex apps, React Navigation is available:

```typescript
// Example with React Navigation (not currently used)
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

type RootStackParamList = {
  Login: undefined;
  Home: undefined;
  ChoreDetail: { choreId: number };
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Home" component={TabNavigator} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

---

## API Integration

### Axios Client Setup

**`api/client.ts`**:

```typescript
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getAPIUrl } from '../config/api';

const TOKEN_KEY = '@chores_tracker:token';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: getAPIUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const token = await AsyncStorage.getItem(TOKEN_KEY);
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error retrieving token:', error);
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired - clear it
      await AsyncStorage.removeItem(TOKEN_KEY);
      // App will redirect to login via AuthContext
    }
    return Promise.reject(error);
  }
);

export { apiClient };
export default apiClient;
```

### Auth API Functions

```typescript
export const authAPI = {
  login: async (username: string, password: string) => {
    // Backend expects form-encoded data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(
      `${getAPIUrl()}/users/login`,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    // Store token
    if (response.data.access_token) {
      await AsyncStorage.setItem(TOKEN_KEY, response.data.access_token);

      // Fetch user data
      const userResponse = await apiClient.get('/users/me');

      return {
        access_token: response.data.access_token,
        token_type: response.data.token_type,
        user: userResponse.data,
      };
    }

    return response.data;
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  logout: async () => {
    await AsyncStorage.removeItem(TOKEN_KEY);
  },

  getToken: async () => {
    return await AsyncStorage.getItem(TOKEN_KEY);
  },

  isAuthenticated: async () => {
    const token = await AsyncStorage.getItem(TOKEN_KEY);
    return !!token;
  },
};
```

### Chores API Module

**`api/chores.ts`**:

```typescript
import apiClient from './client';

export interface Chore {
  id: number;
  title: string;
  description: string;
  reward: number;
  is_completed: boolean;
  is_approved: boolean;
  assignment_mode: 'single' | 'multi_independent' | 'unassigned';
  assignee_ids?: number[];
}

export const choresAPI = {
  // Get available chores for child
  getAvailableChores: async () => {
    const response = await apiClient.get('/chores/available');
    return response.data;
  },

  // Create chore (parent only)
  createChore: async (choreData: Partial<Chore>) => {
    const response = await apiClient.post('/chores/', choreData);
    return response.data;
  },

  // Complete chore
  completeChore: async (choreId: number) => {
    const response = await apiClient.post(`/chores/${choreId}/complete`);
    return response.data;
  },

  // Get pending approvals (parent only)
  getPendingApprovals: async () => {
    const response = await apiClient.get('/chores/pending-approval');
    return response.data;
  },

  // Approve assignment (parent only)
  approveAssignment: async (assignmentId: number, rewardValue?: number) => {
    const response = await apiClient.post(
      `/assignments/${assignmentId}/approve`,
      { reward_value: rewardValue }
    );
    return response.data;
  },

  // Reject assignment (parent only)
  rejectAssignment: async (assignmentId: number, reason: string) => {
    const response = await apiClient.post(
      `/assignments/${assignmentId}/reject`,
      { rejection_reason: reason }
    );
    return response.data;
  },
};
```

### Error Handling Pattern

```typescript
import { Alert } from 'react-native';

const handleAPIError = (error: any, defaultMessage: string) => {
  const message = error.response?.data?.detail || defaultMessage;
  Alert.alert('Error', message);
};

// Usage in component
try {
  await choresAPI.completeChore(choreId);
  Alert.alert('Success', 'Chore completed!');
} catch (error) {
  handleAPIError(error, 'Failed to complete chore');
}
```

---

## Authentication Flow

### AuthContext Implementation

**`contexts/AuthContext.tsx`**:

```typescript
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
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USER_KEY = '@chores_tracker:user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
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
        try {
          // Get fresh user data from API
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
          // API failed, try cached user data
          const storedUser = await AsyncStorage.getItem(USER_KEY);
          if (storedUser) {
            setUser(JSON.parse(storedUser));
            setIsAuthenticated(true);
          } else {
            // No cached data, log out
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
      console.error('Login error:', error);
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
      await AsyncStorage.removeItem(USER_KEY);
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
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
    } catch (error) {
      console.error('Failed to refresh user data:', error);
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
        refreshUser,
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
```

### App Root with Auth

**`src/App.tsx`**:

```typescript
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { SimpleNavigator } from '@/navigation/SimpleNavigator';

const AppContent: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return <SimpleNavigator />;
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <StatusBar style="auto" />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
});
```

### Login Screen Example

**`screens/LoginScreen.tsx`**:

```typescript
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';

interface LoginScreenProps {
  onNavigateToRegister: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onNavigateToRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter both username and password');
      return;
    }

    try {
      setIsLoading(true);
      await login(username, password);
      // Navigation happens automatically via AuthContext state change
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed. Please try again.';
      Alert.alert('Login Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Chores Tracker</Text>
          <Text style={styles.subtitle}>Sign in to your account</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Username</Text>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              placeholder="Enter your username"
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="Enter your password"
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
            />
          </View>

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Sign In</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={onNavigateToRegister}
            disabled={isLoading}
          >
            <Text style={styles.linkText}>
              Don't have an account? Sign Up
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};
```

For complete JWT authentication details, see: [JWT Authentication Guide](../api/JWT_AUTH_EXPLAINER.md)

---

## State Management

### Context API Pattern

The app uses **React Context API** for global state:

```typescript
// Pattern for creating contexts
import React, { createContext, useContext, useState, ReactNode } from 'react';

interface MyContextType {
  value: string;
  setValue: (value: string) => void;
}

const MyContext = createContext<MyContextType | undefined>(undefined);

export const MyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [value, setValue] = useState('');

  return (
    <MyContext.Provider value={{ value, setValue }}>
      {children}
    </MyContext.Provider>
  );
};

export const useMyContext = () => {
  const context = useContext(MyContext);
  if (context === undefined) {
    throw new Error('useMyContext must be used within MyProvider');
  }
  return context;
};
```

### Local Component State

For component-specific state, use `useState`:

```typescript
const ChoreCard: React.FC<{ chore: Chore }> = ({ chore }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <TouchableOpacity onPress={() => setIsExpanded(!isExpanded)}>
      {/* Render chore */}
    </TouchableOpacity>
  );
};
```

### Async Data Fetching Pattern

```typescript
const ChoresScreen: React.FC = () => {
  const [chores, setChores] = useState<Chore[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChores();
  }, []);

  const fetchChores = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await choresAPI.getAvailableChores();
      setChores(data.assigned);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chores');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <ActivityIndicator />;
  }

  if (error) {
    return <Text>Error: {error}</Text>;
  }

  return (
    <FlatList
      data={chores}
      renderItem={({ item }) => <ChoreCard chore={item} />}
      keyExtractor={(item) => item.id.toString()}
    />
  );
};
```

---

## Offline Support

### AsyncStorage for Persistence

**Storing Data**:
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Store object
const saveChores = async (chores: Chore[]) => {
  await AsyncStorage.setItem('@chores', JSON.stringify(chores));
};

// Retrieve object
const loadChores = async (): Promise<Chore[]> => {
  const data = await AsyncStorage.getItem('@chores');
  return data ? JSON.parse(data) : [];
};

// Remove data
const clearChores = async () => {
  await AsyncStorage.removeItem('@chores');
};
```

### Offline-First Pattern

```typescript
const fetchChoresWithCache = async () => {
  try {
    // Try to load from cache first
    const cachedChores = await loadChores();
    if (cachedChores.length > 0) {
      setChores(cachedChores);
    }

    // Then fetch from API
    const freshChores = await choresAPI.getAvailableChores();
    setChores(freshChores.assigned);
    await saveChores(freshChores.assigned);
  } catch (error) {
    // If API fails, use cached data
    console.error('Failed to fetch chores, using cached data', error);
  }
};
```

### Network Status Detection

```typescript
import NetInfo from '@react-native-community/netinfo';

const [isOnline, setIsOnline] = useState(true);

useEffect(() => {
  const unsubscribe = NetInfo.addEventListener(state => {
    setIsOnline(state.isConnected ?? false);
  });

  return () => unsubscribe();
}, []);

// Show offline indicator
{!isOnline && (
  <View style={styles.offlineBanner}>
    <Text>You are offline</Text>
  </View>
)}
```

---

## Component Library

### ChoreCard Component

```typescript
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface Chore {
  id: number;
  title: string;
  description: string;
  reward: number;
  is_completed: boolean;
}

interface ChoreCardProps {
  chore: Chore;
  onComplete?: (choreId: number) => void;
  onPress?: (choreId: number) => void;
}

export const ChoreCard: React.FC<ChoreCardProps> = ({
  chore,
  onComplete,
  onPress
}) => {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onPress?.(chore.id)}
      activeOpacity={0.7}
    >
      <View style={styles.content}>
        <Text style={styles.title}>{chore.title}</Text>
        <Text style={styles.description}>{chore.description}</Text>
        <Text style={styles.reward}>${chore.reward.toFixed(2)}</Text>
      </View>

      {!chore.is_completed && onComplete && (
        <TouchableOpacity
          style={styles.completeButton}
          onPress={() => onComplete(chore.id)}
        >
          <Text style={styles.completeButtonText}>Complete</Text>
        </TouchableOpacity>
      )}

      {chore.is_completed && (
        <View style={styles.completedBadge}>
          <Text style={styles.completedText}>✓ Completed</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  content: {
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  reward: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  completeButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  completeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  completedBadge: {
    backgroundColor: '#E8F5E9',
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
  },
  completedText: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '600',
  },
});
```

### Common UI Components

**Loading Indicator**:
```typescript
export const LoadingScreen: React.FC = () => (
  <View style={styles.loadingContainer}>
    <ActivityIndicator size="large" color="#007AFF" />
    <Text style={styles.loadingText}>Loading...</Text>
  </View>
);
```

**Error Message**:
```typescript
export const ErrorMessage: React.FC<{ message: string; onRetry?: () => void }> = ({
  message,
  onRetry,
}) => (
  <View style={styles.errorContainer}>
    <Text style={styles.errorText}>{message}</Text>
    {onRetry && (
      <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
        <Text style={styles.retryText}>Retry</Text>
      </TouchableOpacity>
    )}
  </View>
);
```

---

## Styling Patterns

### StyleSheet API

```typescript
import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
```

### Design System Constants

```typescript
// constants/theme.ts
export const Colors = {
  primary: '#007AFF',
  secondary: '#5856D6',
  success: '#4CAF50',
  warning: '#FF9500',
  error: '#FF3B30',
  background: '#f5f5f5',
  card: '#ffffff',
  text: '#333333',
  textSecondary: '#666666',
  border: '#e0e0e0',
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const Typography = {
  h1: {
    fontSize: 32,
    fontWeight: 'bold' as const,
  },
  h2: {
    fontSize: 24,
    fontWeight: '600' as const,
  },
  body: {
    fontSize: 16,
    fontWeight: 'normal' as const,
  },
  caption: {
    fontSize: 12,
    fontWeight: 'normal' as const,
  },
};
```

**Usage**:
```typescript
import { Colors, Spacing, Typography } from '@/constants/theme';

const styles = StyleSheet.create({
  header: {
    ...Typography.h1,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  button: {
    backgroundColor: Colors.primary,
    padding: Spacing.md,
    borderRadius: 8,
  },
});
```

### Responsive Layouts

```typescript
import { Dimensions } from 'react-native';

const { width, height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    width: width > 600 ? 600 : '100%', // Max width on tablets
    alignSelf: 'center',
  },
  card: {
    width: width < 400 ? '100%' : 350, // Smaller on phones
  },
});
```

---

## Building and Deployment

### Development Build

```bash
# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Configure project
eas build:configure

# Build for iOS simulator
eas build --platform ios --profile development

# Build for Android emulator
eas build --platform android --profile development
```

### Production Build

**`eas.json`**:
```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "production": {
      "distribution": "store",
      "env": {
        "API_URL": "https://api.chorestracker.com/api/v1"
      }
    }
  }
}
```

**Build Commands**:
```bash
# iOS Production
eas build --platform ios --profile production

# Android Production
eas build --platform android --profile production

# Both platforms
eas build --platform all --profile production
```

### Over-the-Air Updates

```bash
# Publish update without app store review
eas update --branch production --message "Bug fixes and improvements"

# Rollback if needed
eas update:rollback --branch production
```

### App Store Submission

**iOS**:
```bash
eas submit --platform ios
```

**Android**:
```bash
eas submit --platform android
```

---

## Common Patterns

### Pull to Refresh

```typescript
import { RefreshControl, ScrollView } from 'react-native';

const [refreshing, setRefreshing] = useState(false);

const onRefresh = async () => {
  setRefreshing(true);
  await fetchChores();
  setRefreshing(false);
};

<ScrollView
  refreshControl={
    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
  }
>
  {/* Content */}
</ScrollView>
```

### Infinite Scroll

```typescript
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadMore = async () => {
  if (!hasMore) return;

  const nextPage = await fetchChores(page + 1);
  if (nextPage.length === 0) {
    setHasMore(false);
  } else {
    setChores([...chores, ...nextPage]);
    setPage(page + 1);
  }
};

<FlatList
  data={chores}
  renderItem={({ item }) => <ChoreCard chore={item} />}
  onEndReached={loadMore}
  onEndReachedThreshold={0.5}
/>
```

### Form Validation

```typescript
const [errors, setErrors] = useState<Record<string, string>>({});

const validateForm = () => {
  const newErrors: Record<string, string> = {};

  if (!title.trim()) {
    newErrors.title = 'Title is required';
  }

  if (reward <= 0) {
    newErrors.reward = 'Reward must be greater than 0';
  }

  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = async () => {
  if (!validateForm()) return;

  // Submit form
};

{errors.title && (
  <Text style={styles.errorText}>{errors.title}</Text>
)}
```

### Modals

```typescript
import { Modal } from 'react-native';

const [modalVisible, setModalVisible] = useState(false);

<Modal
  animationType="slide"
  transparent={true}
  visible={modalVisible}
  onRequestClose={() => setModalVisible(false)}
>
  <View style={styles.modalContainer}>
    <View style={styles.modalContent}>
      <Text>Modal Content</Text>
      <TouchableOpacity onPress={() => setModalVisible(false)}>
        <Text>Close</Text>
      </TouchableOpacity>
    </View>
  </View>
</Modal>
```

---

## Additional Resources

### Internal Documentation
- [Mobile App Development Guide](./MOBILE_APP_DEVELOPMENT_GUIDE.md)
- [JWT Authentication Guide](../api/JWT_AUTH_EXPLAINER.md)
- [Backend API Documentation](http://localhost:8000/docs)

### External Resources
- **React Native Docs**: https://reactnative.dev/
- **Expo Docs**: https://docs.expo.dev/
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/

### Project Links
- **Repository**: https://github.com/your-org/chores-tracker
- **API Docs**: http://localhost:8000/docs
- **Figma Designs**: [Link to designs]

---

**Last Updated**: 2025-11-23
**React Native Version**: 0.79.5
**Expo SDK**: 53
