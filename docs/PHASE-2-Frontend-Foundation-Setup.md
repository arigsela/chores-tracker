# Phase 2: Frontend Foundation Setup Implementation Plan

**Document Version:** 1.0  
**Date:** January 28, 2025  
**Phase Duration:** 4 weeks  
**Author:** Migration Planner

## Executive Summary

Phase 2 establishes the React frontend foundation, creating a modern SPA architecture that will eventually replace the HTMX implementation. This phase focuses on setting up the development environment, implementing core authentication, creating the component library foundation, and establishing CI/CD pipelines. Special attention is given to making the setup DevOps-engineer-friendly with extensive automation and clear documentation.

## Phase Overview

### Objectives
1. Set up React project with TypeScript and modern tooling
2. Implement JWT authentication flow matching backend
3. Create base layouts and routing structure
4. Establish shared component library foundation
5. Configure API client with proper error handling
6. Set up comprehensive CI/CD pipeline
7. Implement development workflow with hot reloading

### Success Criteria
- [ ] React app running locally with Docker support
- [ ] Authentication flow working end-to-end
- [ ] Base routing structure with protected routes
- [ ] 5+ reusable components in component library
- [ ] API client integrated with backend v2 endpoints
- [ ] CI/CD pipeline deploying to staging
- [ ] Development environment with <3s hot reload
- [ ] 80%+ test coverage for core components

## Detailed Implementation Plan

### Week 1: Project Setup and Tooling (Days 1-5)

#### Day 1: Development Environment Setup
**Tasks:**
1. **Create React Project with Vite** ⬜
   ```bash
   # Create project structure
   cd /Users/arisela/git/chores-tracker
   npm create vite@latest packages/web -- --template react-ts
   
   # Initial folder structure
   packages/
   └── web/
       ├── src/
       │   ├── components/     # Reusable UI components
       │   ├── pages/          # Route-based page components
       │   ├── hooks/          # Custom React hooks
       │   ├── services/       # API service layer
       │   ├── utils/          # Utility functions
       │   ├── types/          # TypeScript types
       │   ├── contexts/       # React contexts
       │   └── styles/         # Global styles
       ├── public/
       ├── tests/
       └── docker/
   ```
   
   **Testing:**
   - Verify project builds successfully
   - Confirm TypeScript configuration

2. **Install Core Dependencies** ⬜
   ```bash
   cd packages/web
   
   # Core React ecosystem
   npm install react-router-dom@^6.21.0
   npm install @tanstack/react-query@^5.17.0
   npm install axios@^1.6.5
   
   # Material-UI
   npm install @mui/material@^5.15.3 @emotion/react@^11.11.3 @emotion/styled@^11.11.0
   npm install @mui/icons-material@^5.15.3
   
   # Form handling
   npm install react-hook-form@^7.48.2 zod@^3.22.4 @hookform/resolvers@^3.3.4
   
   # Development tools
   npm install -D @types/react @types/react-dom @types/node
   npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
   npm install -D prettier eslint-config-prettier eslint-plugin-react-hooks
   npm install -D vitest @testing-library/react @testing-library/jest-dom
   npm install -D @vitejs/plugin-react-swc
   ```
   
   **Deliverables:**
   - package.json with all dependencies
   - Initial project structure

#### Day 2: Development Configuration
**Tasks:**
1. **Configure TypeScript** ⬜
   ```json
   // tsconfig.json
   {
     "compilerOptions": {
       "target": "ES2020",
       "useDefineForClassFields": true,
       "lib": ["ES2020", "DOM", "DOM.Iterable"],
       "module": "ESNext",
       "skipLibCheck": true,
       "moduleResolution": "bundler",
       "allowImportingTsExtensions": true,
       "resolveJsonModule": true,
       "isolatedModules": true,
       "noEmit": true,
       "jsx": "react-jsx",
       "strict": true,
       "noUnusedLocals": true,
       "noUnusedParameters": true,
       "noFallthroughCasesInSwitch": true,
       "paths": {
         "@/*": ["./src/*"],
         "@components/*": ["./src/components/*"],
         "@services/*": ["./src/services/*"]
       }
     },
     "include": ["src"],
     "references": [{ "path": "./tsconfig.node.json" }]
   }
   ```

2. **Setup ESLint and Prettier** ⬜
   ```javascript
   // .eslintrc.cjs
   module.exports = {
     root: true,
     env: { browser: true, es2020: true },
     extends: [
       'eslint:recommended',
       'plugin:@typescript-eslint/recommended',
       'plugin:react-hooks/recommended',
       'prettier'
     ],
     ignorePatterns: ['dist', '.eslintrc.cjs'],
     parser: '@typescript-eslint/parser',
     plugins: ['react-refresh'],
     rules: {
       'react-refresh/only-export-components': [
         'warn',
         { allowConstantExport: true },
       ],
     },
   }
   ```

3. **Configure Vite** ⬜
   ```typescript
   // vite.config.ts
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react-swc'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
         '@components': path.resolve(__dirname, './src/components'),
         '@services': path.resolve(__dirname, './src/services'),
       }
     },
     server: {
       port: 3000,
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         }
       }
     }
   })
   ```

   **Testing:**
   - Run linting: `npm run lint`
   - Verify path aliases work

#### Day 3: Docker Setup
**Tasks:**
1. **Create Development Dockerfile** ⬜
   ```dockerfile
   # packages/web/docker/Dockerfile.dev
   FROM node:20-alpine
   
   WORKDIR /app
   
   # Install dependencies
   COPY package*.json ./
   RUN npm ci
   
   # Copy source
   COPY . .
   
   # Expose port
   EXPOSE 3000
   
   # Start dev server
   CMD ["npm", "run", "dev", "--", "--host"]
   ```

2. **Create Production Dockerfile** ⬜
   ```dockerfile
   # packages/web/docker/Dockerfile
   FROM node:20-alpine as builder
   
   WORKDIR /app
   
   # Install dependencies
   COPY package*.json ./
   RUN npm ci
   
   # Copy source and build
   COPY . .
   RUN npm run build
   
   # Production stage
   FROM nginx:alpine
   
   # Copy built assets
   COPY --from=builder /app/dist /usr/share/nginx/html
   
   # Copy nginx config
   COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
   
   EXPOSE 80
   ```

3. **Update Docker Compose** ⬜
   ```yaml
   # docker-compose.yml (add to existing)
   web:
     build:
       context: ./packages/web
       dockerfile: docker/Dockerfile.dev
     ports:
       - "3000:3000"
     volumes:
       - ./packages/web:/app
       - /app/node_modules
     environment:
       - VITE_API_URL=http://api:8000
     depends_on:
       - api
   ```

   **Testing:**
   - `docker-compose up web`
   - Verify hot reloading works

#### Day 4: Testing Setup
**Tasks:**
1. **Configure Vitest** ⬜
   ```typescript
   // vitest.config.ts
   import { defineConfig } from 'vitest/config'
   import react from '@vitejs/plugin-react-swc'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     test: {
       globals: true,
       environment: 'jsdom',
       setupFiles: './src/test/setup.ts',
       coverage: {
         provider: 'v8',
         reporter: ['text', 'json', 'html'],
         exclude: [
           'node_modules/',
           'src/test/',
         ]
       }
     },
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       }
     }
   })
   ```

2. **Create Test Utilities** ⬜
   ```typescript
   // src/test/setup.ts
   import '@testing-library/jest-dom'
   import { cleanup } from '@testing-library/react'
   import { afterEach } from 'vitest'

   afterEach(() => {
     cleanup()
   })

   // src/test/utils.tsx
   import { ReactElement } from 'react'
   import { render, RenderOptions } from '@testing-library/react'
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   import { BrowserRouter } from 'react-router-dom'

   const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
     const queryClient = new QueryClient({
       defaultOptions: {
         queries: { retry: false },
       },
     })

     return (
       <QueryClientProvider client={queryClient}>
         <BrowserRouter>
           {children}
         </BrowserRouter>
       </QueryClientProvider>
     )
   }

   const customRender = (
     ui: ReactElement,
     options?: Omit<RenderOptions, 'wrapper'>,
   ) => render(ui, { wrapper: AllTheProviders, ...options })

   export * from '@testing-library/react'
   export { customRender as render }
   ```

   **Testing:**
   - Run: `npm test`
   - Verify test runner works

#### Day 5: CI/CD Pipeline
**Tasks:**
1. **Create GitHub Actions Workflow** ⬜
   ```yaml
   # .github/workflows/frontend.yml
   name: Frontend CI/CD

   on:
     push:
       branches: [main, develop]
       paths:
         - 'packages/web/**'
         - '.github/workflows/frontend.yml'
     pull_request:
       branches: [main]
       paths:
         - 'packages/web/**'

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Setup Node.js
           uses: actions/setup-node@v4
           with:
             node-version: '20'
             cache: 'npm'
             cache-dependency-path: packages/web/package-lock.json
         
         - name: Install dependencies
           working-directory: packages/web
           run: npm ci
         
         - name: Run linter
           working-directory: packages/web
           run: npm run lint
         
         - name: Run type check
           working-directory: packages/web
           run: npm run type-check
         
         - name: Run tests
           working-directory: packages/web
           run: npm run test:coverage
         
         - name: Upload coverage
           uses: codecov/codecov-action@v3
           with:
             files: ./packages/web/coverage/coverage-final.json

     build:
       needs: test
       runs-on: ubuntu-latest
       if: github.event_name == 'push'
       steps:
         - uses: actions/checkout@v4
         
         - name: Build Docker image
           run: |
             docker build -t chores-web:${{ github.sha }} \
               -f packages/web/docker/Dockerfile \
               packages/web
         
         - name: Push to registry
           if: github.ref == 'refs/heads/main'
           run: |
             # Add your registry push commands here
             echo "Would push to registry"
   ```

2. **Setup Package Scripts** ⬜
   ```json
   // package.json scripts
   {
     "scripts": {
       "dev": "vite",
       "build": "tsc && vite build",
       "preview": "vite preview",
       "test": "vitest",
       "test:coverage": "vitest run --coverage",
       "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
       "type-check": "tsc --noEmit",
       "format": "prettier --write \"src/**/*.{ts,tsx,json,css}\"",
       "format:check": "prettier --check \"src/**/*.{ts,tsx,json,css}\""
     }
   }
   ```

   **Deliverables:**
   - Working CI/CD pipeline
   - All tests passing

### Week 2: Authentication and Core Structure (Days 6-10)

#### Day 6-7: Authentication Service
**Tasks:**
1. **Create Auth Service** ⬜
   ```typescript
   // src/services/auth.service.ts
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

       const response = await apiClient.post('/api/v1/token', formData, {
         headers: {
           'Content-Type': 'application/x-www-form-urlencoded',
         },
       })

       const { access_token } = response.data
       tokenManager.setToken(access_token)
       
       return this.getCurrentUser()
     },

     async getCurrentUser(): Promise<User> {
       const response = await apiClient.get('/api/v1/users/me')
       return UserSchema.parse(response.data)
     },

     logout() {
       tokenManager.removeToken()
     },

     isAuthenticated() {
       return !!tokenManager.getToken()
     },
   }

   export { apiClient }
   ```

2. **Create Auth Context** ⬜
   ```typescript
   // src/contexts/AuthContext.tsx
   import React, { createContext, useContext, useReducer, useEffect } from 'react'
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

   const AuthContext = createContext<AuthContextValue | null>(null)

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
       } catch (error: any) {
         const message = error.response?.data?.detail || 'Login failed'
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

   export const useAuth = () => {
     const context = useContext(AuthContext)
     if (!context) {
       throw new Error('useAuth must be used within an AuthProvider')
     }
     return context
   }
   ```

   **Testing:**
   - Unit tests for auth service
   - Integration test for login flow

#### Day 8: Routing and Layout
**Tasks:**
1. **Setup Router with Protected Routes** ⬜
   ```typescript
   // src/components/ProtectedRoute.tsx
   import { Navigate, Outlet } from 'react-router-dom'
   import { useAuth } from '@/contexts/AuthContext'
   import { CircularProgress, Box } from '@mui/material'

   interface ProtectedRouteProps {
     requiredRole?: 'parent' | 'child'
   }

   export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requiredRole }) => {
     const { isAuthenticated, isLoading, user } = useAuth()

     if (isLoading) {
       return (
         <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
           <CircularProgress />
         </Box>
       )
     }

     if (!isAuthenticated) {
       return <Navigate to="/login" replace />
     }

     if (requiredRole === 'parent' && !user?.is_parent) {
       return <Navigate to="/unauthorized" replace />
     }

     if (requiredRole === 'child' && user?.is_parent) {
       return <Navigate to="/unauthorized" replace />
     }

     return <Outlet />
   }

   // src/App.tsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom'
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   import { ThemeProvider, CssBaseline } from '@mui/material'
   import { AuthProvider } from '@/contexts/AuthContext'
   import { theme } from '@/styles/theme'
   import { ProtectedRoute } from '@/components/ProtectedRoute'
   import { MainLayout } from '@/layouts/MainLayout'

   // Pages
   import { LoginPage } from '@/pages/auth/LoginPage'
   import { DashboardPage } from '@/pages/DashboardPage'
   import { ChoresPage } from '@/pages/chores/ChoresPage'
   import { NotFoundPage } from '@/pages/NotFoundPage'

   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 5 * 60 * 1000, // 5 minutes
         retry: 1,
       },
     },
   })

   export default function App() {
     return (
       <QueryClientProvider client={queryClient}>
         <ThemeProvider theme={theme}>
           <CssBaseline />
           <BrowserRouter>
             <AuthProvider>
               <Routes>
                 {/* Public routes */}
                 <Route path="/login" element={<LoginPage />} />

                 {/* Protected routes */}
                 <Route element={<ProtectedRoute />}>
                   <Route element={<MainLayout />}>
                     <Route path="/" element={<DashboardPage />} />
                     <Route path="/chores" element={<ChoresPage />} />
                   </Route>
                 </Route>

                 {/* Parent-only routes */}
                 <Route element={<ProtectedRoute requiredRole="parent" />}>
                   <Route element={<MainLayout />}>
                     <Route path="/chores/create" element={<CreateChorePage />} />
                     <Route path="/users" element={<UsersPage />} />
                   </Route>
                 </Route>

                 <Route path="*" element={<NotFoundPage />} />
               </Routes>
             </AuthProvider>
           </BrowserRouter>
         </ThemeProvider>
       </QueryClientProvider>
     )
   }
   ```

2. **Create Main Layout** ⬜
   ```typescript
   // src/layouts/MainLayout.tsx
   import { Outlet, Link, useLocation } from 'react-router-dom'
   import {
     AppBar,
     Box,
     Drawer,
     IconButton,
     List,
     ListItem,
     ListItemButton,
     ListItemIcon,
     ListItemText,
     Toolbar,
     Typography,
     Avatar,
     Menu,
     MenuItem,
   } from '@mui/material'
   import {
     Menu as MenuIcon,
     Dashboard,
     Task,
     People,
     ExitToApp,
   } from '@mui/icons-material'
   import { useState } from 'react'
   import { useAuth } from '@/contexts/AuthContext'

   const drawerWidth = 240

   export const MainLayout: React.FC = () => {
     const [mobileOpen, setMobileOpen] = useState(false)
     const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
     const { user, logout } = useAuth()
     const location = useLocation()

     const navigationItems = [
       { text: 'Dashboard', icon: <Dashboard />, path: '/', roles: ['parent', 'child'] },
       { text: 'Chores', icon: <Task />, path: '/chores', roles: ['parent', 'child'] },
       { text: 'Users', icon: <People />, path: '/users', roles: ['parent'] },
     ].filter(item => 
       item.roles.includes(user?.is_parent ? 'parent' : 'child')
     )

     const drawer = (
       <Box>
         <Toolbar>
           <Typography variant="h6" noWrap>
             Chores Tracker
           </Typography>
         </Toolbar>
         <List>
           {navigationItems.map((item) => (
             <ListItem key={item.text} disablePadding>
               <ListItemButton
                 component={Link}
                 to={item.path}
                 selected={location.pathname === item.path}
               >
                 <ListItemIcon>{item.icon}</ListItemIcon>
                 <ListItemText primary={item.text} />
               </ListItemButton>
             </ListItem>
           ))}
         </List>
       </Box>
     )

     return (
       <Box sx={{ display: 'flex' }}>
         <AppBar
           position="fixed"
           sx={{
             width: { sm: `calc(100% - ${drawerWidth}px)` },
             ml: { sm: `${drawerWidth}px` },
           }}
         >
           <Toolbar>
             <IconButton
               color="inherit"
               edge="start"
               onClick={() => setMobileOpen(!mobileOpen)}
               sx={{ mr: 2, display: { sm: 'none' } }}
             >
               <MenuIcon />
             </IconButton>
             <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
               {navigationItems.find(item => item.path === location.pathname)?.text || 'Chores Tracker'}
             </Typography>
             <Box>
               <IconButton
                 onClick={(e) => setAnchorEl(e.currentTarget)}
                 color="inherit"
               >
                 <Avatar sx={{ width: 32, height: 32 }}>
                   {user?.full_name.charAt(0).toUpperCase()}
                 </Avatar>
               </IconButton>
               <Menu
                 anchorEl={anchorEl}
                 open={Boolean(anchorEl)}
                 onClose={() => setAnchorEl(null)}
               >
                 <MenuItem disabled>
                   <Typography variant="body2">{user?.full_name}</Typography>
                 </MenuItem>
                 <MenuItem onClick={logout}>
                   <ListItemIcon>
                     <ExitToApp fontSize="small" />
                   </ListItemIcon>
                   Logout
                 </MenuItem>
               </Menu>
             </Box>
           </Toolbar>
         </AppBar>
         <Box
           component="nav"
           sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
         >
           <Drawer
             variant="temporary"
             open={mobileOpen}
             onClose={() => setMobileOpen(!mobileOpen)}
             ModalProps={{ keepMounted: true }}
             sx={{
               display: { xs: 'block', sm: 'none' },
               '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
             }}
           >
             {drawer}
           </Drawer>
           <Drawer
             variant="permanent"
             sx={{
               display: { xs: 'none', sm: 'block' },
               '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
             }}
             open
           >
             {drawer}
           </Drawer>
         </Box>
         <Box
           component="main"
           sx={{
             flexGrow: 1,
             p: 3,
             width: { sm: `calc(100% - ${drawerWidth}px)` },
           }}
         >
           <Toolbar />
           <Outlet />
         </Box>
       </Box>
     )
   }
   ```

   **Testing:**
   - Navigation works correctly
   - Role-based menu items

#### Day 9: Login Page
**Tasks:**
1. **Create Login Page** ⬜
   ```typescript
   // src/pages/auth/LoginPage.tsx
   import { useState } from 'react'
   import { useForm } from 'react-hook-form'
   import { zodResolver } from '@hookform/resolvers/zod'
   import { Navigate } from 'react-router-dom'
   import {
     Box,
     Button,
     Container,
     Paper,
     TextField,
     Typography,
     Alert,
     CircularProgress,
   } from '@mui/material'
   import { LoginSchema, LoginData } from '@/services/auth.service'
   import { useAuth } from '@/contexts/AuthContext'

   export const LoginPage: React.FC = () => {
     const { login, isAuthenticated, error: authError } = useAuth()
     const [isSubmitting, setIsSubmitting] = useState(false)

     const {
       register,
       handleSubmit,
       formState: { errors },
     } = useForm<LoginData>({
       resolver: zodResolver(LoginSchema),
     })

     if (isAuthenticated) {
       return <Navigate to="/" replace />
     }

     const onSubmit = async (data: LoginData) => {
       setIsSubmitting(true)
       try {
         await login(data.username, data.password)
       } catch {
         // Error handled in context
       } finally {
         setIsSubmitting(false)
       }
     }

     return (
       <Container component="main" maxWidth="xs">
         <Box
           sx={{
             marginTop: 8,
             display: 'flex',
             flexDirection: 'column',
             alignItems: 'center',
           }}
         >
           <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
             <Typography component="h1" variant="h5" align="center">
               Chores Tracker
             </Typography>
             <Typography component="h2" variant="h6" align="center" color="text.secondary" sx={{ mb: 3 }}>
               Sign in to your account
             </Typography>

             {authError && (
               <Alert severity="error" sx={{ mb: 2 }}>
                 {authError}
               </Alert>
             )}

             <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
               <TextField
                 margin="normal"
                 required
                 fullWidth
                 id="username"
                 label="Username"
                 autoComplete="username"
                 autoFocus
                 error={!!errors.username}
                 helperText={errors.username?.message}
                 {...register('username')}
               />
               <TextField
                 margin="normal"
                 required
                 fullWidth
                 label="Password"
                 type="password"
                 id="password"
                 autoComplete="current-password"
                 error={!!errors.password}
                 helperText={errors.password?.message}
                 {...register('password')}
               />
               <Button
                 type="submit"
                 fullWidth
                 variant="contained"
                 sx={{ mt: 3, mb: 2 }}
                 disabled={isSubmitting}
               >
                 {isSubmitting ? <CircularProgress size={24} /> : 'Sign In'}
               </Button>
             </Box>

             <Box sx={{ mt: 2 }}>
               <Typography variant="body2" color="text.secondary" align="center">
                 Demo Accounts:
               </Typography>
               <Typography variant="caption" color="text.secondary" display="block" align="center">
                 Parent: john_doe / Test123!
               </Typography>
               <Typography variant="caption" color="text.secondary" display="block" align="center">
                 Child: alice_doe / Test123!
               </Typography>
             </Box>
           </Paper>
         </Box>
       </Container>
     )
   }
   ```

2. **Create Theme Configuration** ⬜
   ```typescript
   // src/styles/theme.ts
   import { createTheme } from '@mui/material/styles'

   export const theme = createTheme({
     palette: {
       primary: {
         main: '#1976d2',
       },
       secondary: {
         main: '#dc004e',
       },
       success: {
         main: '#2e7d32',
       },
     },
     typography: {
       fontFamily: [
         '-apple-system',
         'BlinkMacSystemFont',
         '"Segoe UI"',
         'Roboto',
         '"Helvetica Neue"',
         'Arial',
         'sans-serif',
       ].join(','),
     },
     components: {
       MuiButton: {
         styleOverrides: {
           root: {
             textTransform: 'none',
           },
         },
       },
       MuiDrawer: {
         styleOverrides: {
           paper: {
             backgroundColor: '#f5f5f5',
           },
         },
       },
     },
   })
   ```

   **Testing:**
   - Login form validation
   - Successful login redirects
   - Error handling

#### Day 10: API Client Setup
**Tasks:**
1. **Create Base API Service** ⬜
   ```typescript
   // src/services/api.service.ts
   import { apiClient } from './auth.service'
   import { z } from 'zod'

   // Base schemas
   export const PaginationSchema = z.object({
     page: z.number().default(1),
     per_page: z.number().default(20),
     total: z.number(),
     total_pages: z.number(),
   })

   export const StandardResponseSchema = <T extends z.ZodType>(dataSchema: T) =>
     z.object({
       success: z.boolean(),
       data: dataSchema.optional(),
       error: z.object({
         code: z.string(),
         message: z.string(),
         details: z.array(z.any()).optional(),
       }).optional(),
       metadata: z.object({
         timestamp: z.string(),
         version: z.string(),
         request_id: z.string(),
       }).optional(),
     })

   // Error handling
   export class ApiError extends Error {
     constructor(
       public code: string,
       message: string,
       public details?: any
     ) {
       super(message)
       this.name = 'ApiError'
     }
   }

   // Generic API methods
   export const api = {
     async get<T>(url: string, schema: z.ZodType<T>) {
       try {
         const response = await apiClient.get(url)
         return schema.parse(response.data)
       } catch (error: any) {
         throw this.handleError(error)
       }
     },

     async post<T>(url: string, data: any, schema: z.ZodType<T>) {
       try {
         const response = await apiClient.post(url, data)
         return schema.parse(response.data)
       } catch (error: any) {
         throw this.handleError(error)
       }
     },

     async put<T>(url: string, data: any, schema: z.ZodType<T>) {
       try {
         const response = await apiClient.put(url, data)
         return schema.parse(response.data)
       } catch (error: any) {
         throw this.handleError(error)
       }
     },

     async delete(url: string) {
       try {
         await apiClient.delete(url)
       } catch (error: any) {
         throw this.handleError(error)
       }
     },

     handleError(error: any): ApiError {
       if (error.response?.data?.error) {
         const { code, message, details } = error.response.data.error
         return new ApiError(code || 'UNKNOWN_ERROR', message || 'An error occurred', details)
       }
       return new ApiError('NETWORK_ERROR', error.message || 'Network error occurred')
     },
   }
   ```

2. **Create Chore Service** ⬜
   ```typescript
   // src/services/chore.service.ts
   import { z } from 'zod'
   import { api } from './api.service'
   import { UserSchema } from './auth.service'

   // Chore schemas
   export const ChoreSchema = z.object({
     id: z.number(),
     title: z.string(),
     description: z.string(),
     reward_min: z.number(),
     reward_max: z.number().nullable(),
     status: z.enum(['created', 'pending', 'approved', 'disabled']),
     recurrence: z.enum(['once', 'daily', 'weekly', 'monthly']).nullable(),
     created_at: z.string(),
     updated_at: z.string(),
     assignee: UserSchema.nullable(),
     created_by: UserSchema,
   })

   export const CreateChoreSchema = z.object({
     title: z.string().min(1, 'Title is required'),
     description: z.string().min(1, 'Description is required'),
     reward_min: z.number().min(0, 'Minimum reward must be positive'),
     reward_max: z.number().min(0).nullable(),
     assignee_id: z.number(),
     recurrence: z.enum(['once', 'daily', 'weekly', 'monthly']).nullable(),
   })

   export type Chore = z.infer<typeof ChoreSchema>
   export type CreateChoreData = z.infer<typeof CreateChoreSchema>

   export const choreService = {
     async getChores() {
       return api.get('/api/v2/chores/', z.array(ChoreSchema))
     },

     async getChore(id: number) {
       return api.get(`/api/v2/chores/${id}`, ChoreSchema)
     },

     async createChore(data: CreateChoreData) {
       return api.post('/api/v2/chores/', data, ChoreSchema)
     },

     async updateChore(id: number, data: Partial<CreateChoreData>) {
       return api.put(`/api/v2/chores/${id}`, data, ChoreSchema)
     },

     async deleteChore(id: number) {
       return api.delete(`/api/v2/chores/${id}`)
     },

     async completeChore(id: number) {
       return api.post(`/api/v2/chores/${id}/complete`, {}, ChoreSchema)
     },

     async approveChore(id: number, rewardAmount: number) {
       return api.post(
         `/api/v2/chores/${id}/approve`,
         { reward_amount: rewardAmount },
         ChoreSchema
       )
     },

     async getAvailableChores() {
       return api.get('/api/v2/chores/available', z.array(ChoreSchema))
     },

     async getPendingApproval() {
       return api.get('/api/v2/chores/pending-approval', z.array(ChoreSchema))
     },
   }
   ```

   **Testing:**
   - API error handling
   - Schema validation
   - Service method tests

### Week 3: Component Library and State Management (Days 11-15)

#### Day 11-12: Core Components
**Tasks:**
1. **Create Loading Component** ⬜
   ```typescript
   // src/components/common/Loading.tsx
   import { Box, CircularProgress, Typography } from '@mui/material'

   interface LoadingProps {
     message?: string
     fullScreen?: boolean
   }

   export const Loading: React.FC<LoadingProps> = ({ 
     message = 'Loading...', 
     fullScreen = false 
   }) => {
     const content = (
       <Box
         display="flex"
         flexDirection="column"
         alignItems="center"
         justifyContent="center"
         gap={2}
       >
         <CircularProgress />
         <Typography variant="body2" color="text.secondary">
           {message}
         </Typography>
       </Box>
     )

     if (fullScreen) {
       return (
         <Box
           position="fixed"
           top={0}
           left={0}
           right={0}
           bottom={0}
           display="flex"
           alignItems="center"
           justifyContent="center"
           bgcolor="background.default"
           zIndex={9999}
         >
           {content}
         </Box>
       )
     }

     return content
   }
   ```

2. **Create Error Boundary** ⬜
   ```typescript
   // src/components/common/ErrorBoundary.tsx
   import React, { Component, ErrorInfo, ReactNode } from 'react'
   import { Box, Typography, Button, Paper } from '@mui/material'
   import { ErrorOutline } from '@mui/icons-material'

   interface Props {
     children: ReactNode
     fallback?: ReactNode
   }

   interface State {
     hasError: boolean
     error: Error | null
   }

   export class ErrorBoundary extends Component<Props, State> {
     public state: State = {
       hasError: false,
       error: null,
     }

     public static getDerivedStateFromError(error: Error): State {
       return { hasError: true, error }
     }

     public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
       console.error('Uncaught error:', error, errorInfo)
     }

     private handleReset = () => {
       this.setState({ hasError: false, error: null })
       window.location.href = '/'
     }

     public render() {
       if (this.state.hasError) {
         if (this.props.fallback) {
           return this.props.fallback
         }

         return (
           <Box
             display="flex"
             alignItems="center"
             justifyContent="center"
             minHeight="100vh"
             p={3}
           >
             <Paper elevation={3} sx={{ p: 4, maxWidth: 500 }}>
               <Box display="flex" alignItems="center" gap={2} mb={2}>
                 <ErrorOutline color="error" fontSize="large" />
                 <Typography variant="h5">Something went wrong</Typography>
               </Box>
               <Typography variant="body1" color="text.secondary" mb={3}>
                 An unexpected error occurred. Please try refreshing the page.
               </Typography>
               {this.state.error && (
                 <Typography
                   variant="caption"
                   component="pre"
                   sx={{
                     p: 2,
                     bgcolor: 'grey.100',
                     borderRadius: 1,
                     overflow: 'auto',
                     mb: 3,
                   }}
                 >
                   {this.state.error.message}
                 </Typography>
               )}
               <Button
                 variant="contained"
                 onClick={this.handleReset}
                 fullWidth
               >
                 Return to Dashboard
               </Button>
             </Paper>
           </Box>
         )
       }

       return this.props.children
     }
   }
   ```

3. **Create Confirmation Dialog** ⬜
   ```typescript
   // src/components/common/ConfirmDialog.tsx
   import {
     Dialog,
     DialogTitle,
     DialogContent,
     DialogContentText,
     DialogActions,
     Button,
   } from '@mui/material'

   interface ConfirmDialogProps {
     open: boolean
     title: string
     message: string
     confirmText?: string
     cancelText?: string
     onConfirm: () => void
     onCancel: () => void
     severity?: 'info' | 'warning' | 'error'
   }

   export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
     open,
     title,
     message,
     confirmText = 'Confirm',
     cancelText = 'Cancel',
     onConfirm,
     onCancel,
     severity = 'info',
   }) => {
     const getConfirmColor = () => {
       switch (severity) {
         case 'error':
           return 'error'
         case 'warning':
           return 'warning'
         default:
           return 'primary'
       }
     }

     return (
       <Dialog
         open={open}
         onClose={onCancel}
         aria-labelledby="confirm-dialog-title"
         aria-describedby="confirm-dialog-description"
       >
         <DialogTitle id="confirm-dialog-title">{title}</DialogTitle>
         <DialogContent>
           <DialogContentText id="confirm-dialog-description">
             {message}
           </DialogContentText>
         </DialogContent>
         <DialogActions>
           <Button onClick={onCancel} color="inherit">
             {cancelText}
           </Button>
           <Button onClick={onConfirm} color={getConfirmColor()} autoFocus>
             {confirmText}
           </Button>
         </DialogActions>
       </Dialog>
     )
   }
   ```

#### Day 13: Form Components
**Tasks:**
1. **Create Form Input Components** ⬜
   ```typescript
   // src/components/form/FormTextField.tsx
   import { TextField, TextFieldProps } from '@mui/material'
   import { Controller, Control, FieldPath, FieldValues } from 'react-hook-form'

   interface FormTextFieldProps<T extends FieldValues>
     extends Omit<TextFieldProps, 'name'> {
     name: FieldPath<T>
     control: Control<T>
   }

   export function FormTextField<T extends FieldValues>({
     name,
     control,
     ...textFieldProps
   }: FormTextFieldProps<T>) {
     return (
       <Controller
         name={name}
         control={control}
         render={({ field, fieldState: { error } }) => (
           <TextField
             {...field}
             {...textFieldProps}
             error={!!error}
             helperText={error?.message || textFieldProps.helperText}
           />
         )}
       />
     )
   }

   // src/components/form/FormSelect.tsx
   import {
     FormControl,
     InputLabel,
     Select,
     MenuItem,
     FormHelperText,
     SelectProps,
   } from '@mui/material'
   import { Controller, Control, FieldPath, FieldValues } from 'react-hook-form'

   interface FormSelectProps<T extends FieldValues>
     extends Omit<SelectProps, 'name'> {
     name: FieldPath<T>
     control: Control<T>
     label: string
     options: Array<{ value: string | number; label: string }>
     helperText?: string
   }

   export function FormSelect<T extends FieldValues>({
     name,
     control,
     label,
     options,
     helperText,
     ...selectProps
   }: FormSelectProps<T>) {
     return (
       <Controller
         name={name}
         control={control}
         render={({ field, fieldState: { error } }) => (
           <FormControl fullWidth error={!!error}>
             <InputLabel>{label}</InputLabel>
             <Select {...field} {...selectProps} label={label}>
               {options.map((option) => (
                 <MenuItem key={option.value} value={option.value}>
                   {option.label}
                 </MenuItem>
               ))}
             </Select>
             {(error?.message || helperText) && (
               <FormHelperText>
                 {error?.message || helperText}
               </FormHelperText>
             )}
           </FormControl>
         )}
       />
     )
   }
   ```

2. **Create Money Input Component** ⬜
   ```typescript
   // src/components/form/MoneyInput.tsx
   import { InputAdornment } from '@mui/material'
   import { Controller, Control, FieldPath, FieldValues } from 'react-hook-form'
   import { FormTextField } from './FormTextField'

   interface MoneyInputProps<T extends FieldValues> {
     name: FieldPath<T>
     control: Control<T>
     label: string
     required?: boolean
     disabled?: boolean
   }

   export function MoneyInput<T extends FieldValues>({
     name,
     control,
     label,
     required,
     disabled,
   }: MoneyInputProps<T>) {
     return (
       <Controller
         name={name}
         control={control}
         render={({ field: { onChange, value, ...field } }) => (
           <FormTextField
             {...field}
             control={control}
             name={name}
             label={label}
             type="number"
             required={required}
             disabled={disabled}
             value={value || ''}
             onChange={(e) => {
               const val = e.target.value
               onChange(val === '' ? null : parseFloat(val))
             }}
             InputProps={{
               startAdornment: (
                 <InputAdornment position="start">$</InputAdornment>
               ),
               inputProps: {
                 min: 0,
                 step: 0.01,
               },
             }}
           />
         )}
       />
     )
   }
   ```

   **Testing:**
   - Form validation
   - Input masking
   - Accessibility

#### Day 14: Custom Hooks
**Tasks:**
1. **Create Data Fetching Hooks** ⬜
   ```typescript
   // src/hooks/useChores.ts
   import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
   import { choreService, Chore, CreateChoreData } from '@/services/chore.service'
   import { useAuth } from '@/contexts/AuthContext'

   export const useChores = () => {
     return useQuery({
       queryKey: ['chores'],
       queryFn: choreService.getChores,
     })
   }

   export const useChore = (id: number) => {
     return useQuery({
       queryKey: ['chores', id],
       queryFn: () => choreService.getChore(id),
       enabled: !!id,
     })
   }

   export const useAvailableChores = () => {
     const { user } = useAuth()
     return useQuery({
       queryKey: ['chores', 'available'],
       queryFn: choreService.getAvailableChores,
       enabled: !user?.is_parent,
     })
   }

   export const usePendingChores = () => {
     const { user } = useAuth()
     return useQuery({
       queryKey: ['chores', 'pending'],
       queryFn: choreService.getPendingApproval,
       enabled: user?.is_parent,
     })
   }

   export const useCreateChore = () => {
     const queryClient = useQueryClient()
     
     return useMutation({
       mutationFn: (data: CreateChoreData) => choreService.createChore(data),
       onSuccess: () => {
         queryClient.invalidateQueries({ queryKey: ['chores'] })
       },
     })
   }

   export const useCompleteChore = () => {
     const queryClient = useQueryClient()
     
     return useMutation({
       mutationFn: (id: number) => choreService.completeChore(id),
       onSuccess: (_, id) => {
         queryClient.invalidateQueries({ queryKey: ['chores'] })
         queryClient.invalidateQueries({ queryKey: ['chores', id] })
       },
     })
   }

   export const useApproveChore = () => {
     const queryClient = useQueryClient()
     
     return useMutation({
       mutationFn: ({ id, amount }: { id: number; amount: number }) =>
         choreService.approveChore(id, amount),
       onSuccess: (_, { id }) => {
         queryClient.invalidateQueries({ queryKey: ['chores'] })
         queryClient.invalidateQueries({ queryKey: ['chores', id] })
         queryClient.invalidateQueries({ queryKey: ['chores', 'pending'] })
       },
     })
   }
   ```

2. **Create Utility Hooks** ⬜
   ```typescript
   // src/hooks/useDebounce.ts
   import { useState, useEffect } from 'react'

   export function useDebounce<T>(value: T, delay: number): T {
     const [debouncedValue, setDebouncedValue] = useState<T>(value)

     useEffect(() => {
       const handler = setTimeout(() => {
         setDebouncedValue(value)
       }, delay)

       return () => {
         clearTimeout(handler)
       }
     }, [value, delay])

     return debouncedValue
   }

   // src/hooks/useLocalStorage.ts
   import { useState, useEffect } from 'react'

   export function useLocalStorage<T>(
     key: string,
     initialValue: T
   ): [T, (value: T | ((val: T) => T)) => void] {
     const [storedValue, setStoredValue] = useState<T>(() => {
       try {
         const item = window.localStorage.getItem(key)
         return item ? JSON.parse(item) : initialValue
       } catch (error) {
         console.error(`Error reading localStorage key "${key}":`, error)
         return initialValue
       }
     })

     const setValue = (value: T | ((val: T) => T)) => {
       try {
         const valueToStore = value instanceof Function ? value(storedValue) : value
         setStoredValue(valueToStore)
         window.localStorage.setItem(key, JSON.stringify(valueToStore))
       } catch (error) {
         console.error(`Error setting localStorage key "${key}":`, error)
       }
     }

     return [storedValue, setValue]
   }

   // src/hooks/useToast.ts
   import { useSnackbar, VariantType } from 'notistack'

   export const useToast = () => {
     const { enqueueSnackbar } = useSnackbar()

     const toast = {
       success: (message: string) => 
         enqueueSnackbar(message, { variant: 'success' }),
       error: (message: string) => 
         enqueueSnackbar(message, { variant: 'error' }),
       warning: (message: string) => 
         enqueueSnackbar(message, { variant: 'warning' }),
       info: (message: string) => 
         enqueueSnackbar(message, { variant: 'info' }),
     }

     return toast
   }
   ```

   **Testing:**
   - Hook behavior tests
   - Edge case handling

#### Day 15: Dashboard Page
**Tasks:**
1. **Create Dashboard Page** ⬜
   ```typescript
   // src/pages/DashboardPage.tsx
   import { Grid, Card, CardContent, Typography, Box } from '@mui/material'
   import { Assignment, CheckCircle, HourglassEmpty, AttachMoney } from '@mui/icons-material'
   import { useAuth } from '@/contexts/AuthContext'
   import { useChores, usePendingChores } from '@/hooks/useChores'
   import { Loading } from '@/components/common/Loading'
   import { ChoreCard } from '@/components/chores/ChoreCard'

   export const DashboardPage: React.FC = () => {
     const { user } = useAuth()
     const { data: chores, isLoading } = useChores()
     const { data: pendingChores } = usePendingChores()

     if (isLoading) {
       return <Loading message="Loading dashboard..." />
     }

     const stats = {
       total: chores?.length || 0,
       completed: chores?.filter(c => c.status === 'approved').length || 0,
       pending: chores?.filter(c => c.status === 'pending').length || 0,
       earnings: chores
         ?.filter(c => c.status === 'approved')
         .reduce((sum, c) => sum + c.reward_min, 0) || 0,
     }

     return (
       <Box>
         <Typography variant="h4" gutterBottom>
           Welcome back, {user?.full_name}!
         </Typography>

         <Grid container spacing={3} sx={{ mb: 4 }}>
           <Grid item xs={12} sm={6} md={3}>
             <Card>
               <CardContent>
                 <Box display="flex" alignItems="center" gap={1}>
                   <Assignment color="primary" />
                   <Typography color="text.secondary" gutterBottom>
                     Total Chores
                   </Typography>
                 </Box>
                 <Typography variant="h4">{stats.total}</Typography>
               </CardContent>
             </Card>
           </Grid>

           <Grid item xs={12} sm={6} md={3}>
             <Card>
               <CardContent>
                 <Box display="flex" alignItems="center" gap={1}>
                   <CheckCircle color="success" />
                   <Typography color="text.secondary" gutterBottom>
                     Completed
                   </Typography>
                 </Box>
                 <Typography variant="h4">{stats.completed}</Typography>
               </CardContent>
             </Card>
           </Grid>

           <Grid item xs={12} sm={6} md={3}>
             <Card>
               <CardContent>
                 <Box display="flex" alignItems="center" gap={1}>
                   <HourglassEmpty color="warning" />
                   <Typography color="text.secondary" gutterBottom>
                     Pending
                   </Typography>
                 </Box>
                 <Typography variant="h4">{stats.pending}</Typography>
               </CardContent>
             </Card>
           </Grid>

           <Grid item xs={12} sm={6} md={3}>
             <Card>
               <CardContent>
                 <Box display="flex" alignItems="center" gap={1}>
                   <AttachMoney color="success" />
                   <Typography color="text.secondary" gutterBottom>
                     Earnings
                   </Typography>
                 </Box>
                 <Typography variant="h4">${stats.earnings.toFixed(2)}</Typography>
               </CardContent>
             </Card>
           </Grid>
         </Grid>

         {user?.is_parent && pendingChores && pendingChores.length > 0 && (
           <Box mb={4}>
             <Typography variant="h5" gutterBottom>
               Chores Awaiting Approval
             </Typography>
             <Grid container spacing={2}>
               {pendingChores.map((chore) => (
                 <Grid item xs={12} md={6} key={chore.id}>
                   <ChoreCard chore={chore} showActions />
                 </Grid>
               ))}
             </Grid>
           </Box>
         )}

         {!user?.is_parent && (
           <Box>
             <Typography variant="h5" gutterBottom>
               Your Active Chores
             </Typography>
             <Grid container spacing={2}>
               {chores
                 ?.filter(c => c.status === 'created' && c.assignee?.id === user.id)
                 .map((chore) => (
                   <Grid item xs={12} md={6} key={chore.id}>
                     <ChoreCard chore={chore} showActions />
                   </Grid>
                 ))}
             </Grid>
           </Box>
         )}
       </Box>
     )
   }
   ```

2. **Create Chore Card Component** ⬜
   ```typescript
   // src/components/chores/ChoreCard.tsx
   import {
     Card,
     CardContent,
     CardActions,
     Typography,
     Chip,
     Button,
     Box,
   } from '@mui/material'
   import { Chore } from '@/services/chore.service'
   import { useAuth } from '@/contexts/AuthContext'
   import { useCompleteChore } from '@/hooks/useChores'
   import { useToast } from '@/hooks/useToast'

   interface ChoreCardProps {
     chore: Chore
     showActions?: boolean
   }

   export const ChoreCard: React.FC<ChoreCardProps> = ({ chore, showActions }) => {
     const { user } = useAuth()
     const completeChore = useCompleteChore()
     const toast = useToast()

     const handleComplete = async () => {
       try {
         await completeChore.mutateAsync(chore.id)
         toast.success('Chore marked as complete!')
       } catch (error) {
         toast.error('Failed to complete chore')
       }
     }

     const getStatusColor = () => {
       switch (chore.status) {
         case 'created':
           return 'primary'
         case 'pending':
           return 'warning'
         case 'approved':
           return 'success'
         default:
           return 'default'
       }
     }

     const canComplete = 
       !user?.is_parent && 
       chore.status === 'created' && 
       chore.assignee?.id === user?.id

     return (
       <Card>
         <CardContent>
           <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
             <Typography variant="h6" component="div">
               {chore.title}
             </Typography>
             <Chip
               label={chore.status}
               size="small"
               color={getStatusColor()}
             />
           </Box>
           
           <Typography variant="body2" color="text.secondary" paragraph>
             {chore.description}
           </Typography>

           <Box display="flex" gap={2} alignItems="center">
             <Typography variant="body2">
               Reward: ${chore.reward_min}
               {chore.reward_max && ` - $${chore.reward_max}`}
             </Typography>
             {chore.recurrence && (
               <Chip label={chore.recurrence} size="small" variant="outlined" />
             )}
           </Box>

           {chore.assignee && (
             <Typography variant="caption" display="block" mt={1}>
               Assigned to: {chore.assignee.full_name}
             </Typography>
           )}
         </CardContent>

         {showActions && (
           <CardActions>
             {canComplete && (
               <Button
                 size="small"
                 onClick={handleComplete}
                 disabled={completeChore.isPending}
               >
                 Mark Complete
               </Button>
             )}
             {user?.is_parent && chore.status === 'pending' && (
               <Button size="small" color="success">
                 Approve
               </Button>
             )}
           </CardActions>
         )}
       </Card>
     )
   }
   ```

   **Testing:**
   - Component renders correctly
   - User interactions work
   - State updates properly

### Week 4: Integration and Production Setup (Days 16-20)

#### Day 16-17: Integration Testing
**Tasks:**
1. **End-to-End Test Setup** ⬜
   ```typescript
   // tests/e2e/auth.test.ts
   import { test, expect } from '@playwright/test'

   test.describe('Authentication Flow', () => {
     test('should login successfully as parent', async ({ page }) => {
       await page.goto('http://localhost:3000/login')
       
       await page.fill('input[name="username"]', 'john_doe')
       await page.fill('input[name="password"]', 'Test123!')
       await page.click('button[type="submit"]')

       await expect(page).toHaveURL('http://localhost:3000/')
       await expect(page.locator('h4')).toContainText('Welcome back')
     })

     test('should logout successfully', async ({ page }) => {
       // Login first
       await page.goto('http://localhost:3000/login')
       await page.fill('input[name="username"]', 'john_doe')
       await page.fill('input[name="password"]', 'Test123!')
       await page.click('button[type="submit"]')

       // Logout
       await page.click('[aria-label="Account menu"]')
       await page.click('text=Logout')

       await expect(page).toHaveURL('http://localhost:3000/login')
     })

     test('should redirect to login when not authenticated', async ({ page }) => {
       await page.goto('http://localhost:3000/chores')
       await expect(page).toHaveURL('http://localhost:3000/login')
     })
   })
   ```

2. **Integration Test Suite** ⬜
   ```bash
   # Add Playwright
   npm install -D @playwright/test
   npx playwright install

   # playwright.config.ts
   import { defineConfig } from '@playwright/test'

   export default defineConfig({
     testDir: './tests/e2e',
     timeout: 30000,
     use: {
       baseURL: 'http://localhost:3000',
       screenshot: 'only-on-failure',
     },
     webServer: {
       command: 'npm run dev',
       port: 3000,
       reuseExistingServer: !process.env.CI,
     },
   })
   ```

   **Testing:**
   - Run full E2E suite
   - Verify all flows work

#### Day 18: Performance Optimization
**Tasks:**
1. **Bundle Optimization** ⬜
   ```typescript
   // vite.config.ts (updated)
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react-swc'
   import { visualizer } from 'rollup-plugin-visualizer'

   export default defineConfig({
     plugins: [
       react(),
       visualizer({
         open: true,
         gzipSize: true,
         brotliSize: true,
       }),
     ],
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             'react-vendor': ['react', 'react-dom', 'react-router-dom'],
             'mui-vendor': ['@mui/material', '@emotion/react', '@emotion/styled'],
             'utils': ['axios', 'zod', '@tanstack/react-query'],
           },
         },
       },
       chunkSizeWarningLimit: 1000,
     },
   })
   ```

2. **Lazy Loading Setup** ⬜
   ```typescript
   // src/App.tsx (updated with lazy loading)
   import { lazy, Suspense } from 'react'
   import { Loading } from '@/components/common/Loading'

   // Lazy load pages
   const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
   const ChoresPage = lazy(() => import('@/pages/chores/ChoresPage'))
   const CreateChorePage = lazy(() => import('@/pages/chores/CreateChorePage'))
   const UsersPage = lazy(() => import('@/pages/users/UsersPage'))

   // In routes
   <Route path="/" element={
     <Suspense fallback={<Loading fullScreen />}>
       <DashboardPage />
     </Suspense>
   } />
   ```

   **Metrics:**
   - Bundle size < 200KB gzipped
   - Initial load < 3s
   - TTI < 5s

#### Day 19: Documentation
**Tasks:**
1. **Create Developer Guide** ⬜
   ```markdown
   # packages/web/README.md
   # Chores Tracker React Frontend

   ## Quick Start

   ```bash
   # Install dependencies
   npm install

   # Start development server
   npm run dev

   # Run tests
   npm test

   # Build for production
   npm run build
   ```

   ## Project Structure
   ```
   src/
   ├── components/     # Reusable UI components
   ├── pages/          # Page components
   ├── services/       # API services
   ├── hooks/          # Custom React hooks
   ├── contexts/       # React contexts
   ├── utils/          # Utility functions
   └── types/          # TypeScript types
   ```

   ## Key Technologies
   - React 18 with TypeScript
   - Material-UI for components
   - React Query for data fetching
   - React Hook Form for forms
   - Vite for build tooling

   ## Development Workflow

   ### Adding a New Page
   1. Create page component in `src/pages/`
   2. Add route in `src/App.tsx`
   3. Update navigation if needed

   ### Adding a New API Service
   1. Define schemas in service file
   2. Create service methods
   3. Create corresponding hooks
   4. Use hooks in components

   ### Testing
   - Unit tests: `npm test`
   - E2E tests: `npm run test:e2e`
   - Coverage: `npm run test:coverage`
   ```

2. **API Integration Guide** ⬜
   - Document all API endpoints
   - Show usage examples
   - Error handling patterns

   **Deliverables:**
   - Complete documentation
   - Code examples

#### Day 20: Deployment Setup
**Tasks:**
1. **Production Build Pipeline** ⬜
   ```yaml
   # .github/workflows/frontend-deploy.yml
   name: Deploy Frontend

   on:
     push:
       branches: [main]
       paths:
         - 'packages/web/**'

   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Setup Node.js
           uses: actions/setup-node@v4
           with:
             node-version: '20'
         
         - name: Install and Build
           working-directory: packages/web
           run: |
             npm ci
             npm run build
         
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: us-east-1
         
         - name: Deploy to S3
           run: |
             aws s3 sync packages/web/dist s3://${{ secrets.S3_BUCKET }} --delete
             aws cloudfront create-invalidation \
               --distribution-id ${{ secrets.CLOUDFRONT_ID }} \
               --paths "/*"
   ```

2. **Nginx Configuration** ⬜
   ```nginx
   # docker/nginx.conf
   server {
       listen 80;
       server_name _;
       root /usr/share/nginx/html;
       index index.html;

       # Gzip compression
       gzip on;
       gzip_types text/plain text/css text/javascript application/javascript application/json;
       gzip_min_length 1000;

       # Cache static assets
       location /assets/ {
           expires 1y;
           add_header Cache-Control "public, immutable";
       }

       # API proxy
       location /api/ {
           proxy_pass http://api:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       # React app
       location / {
           try_files $uri $uri/ /index.html;
           add_header Cache-Control "no-cache, no-store, must-revalidate";
       }
   }
   ```

   **Testing:**
   - Deploy to staging
   - Verify all features work
   - Performance testing

## Technical Specifications

### Folder Structure
```
packages/web/
├── src/
│   ├── components/
│   │   ├── common/         # Loading, ErrorBoundary, etc.
│   │   ├── form/           # Form components
│   │   ├── chores/         # Chore-specific components
│   │   └── users/          # User-specific components
│   ├── pages/
│   │   ├── auth/           # Login, Register
│   │   ├── chores/         # Chore pages
│   │   └── users/          # User management
│   ├── services/
│   │   ├── api.service.ts  # Base API client
│   │   ├── auth.service.ts # Authentication
│   │   └── chore.service.ts # Chore operations
│   ├── hooks/              # Custom React hooks
│   ├── contexts/           # React contexts
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript types
│   └── styles/             # Global styles
├── public/                 # Static assets
├── tests/
│   ├── unit/              # Unit tests
│   └── e2e/               # E2E tests
└── docker/                # Docker configs
```

### Key Design Decisions

1. **State Management**
   - Start with React Context for auth
   - React Query for server state
   - Local state for UI state
   - Migrate to Redux Toolkit if needed

2. **Component Architecture**
   - Presentational/Container pattern
   - Compound components for complex UI
   - Controlled form components
   - Error boundaries at route level

3. **Testing Strategy**
   - Unit tests for utilities and hooks
   - Integration tests for services
   - Component tests with React Testing Library
   - E2E tests for critical paths

4. **Performance Strategy**
   - Code splitting by route
   - Lazy load heavy components
   - Optimize bundle size
   - Cache API responses

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Learning curve for React | High | Medium | Extensive documentation, pair programming |
| Bundle size too large | Medium | High | Aggressive code splitting, monitoring |
| API integration issues | Low | High | Comprehensive testing, error handling |
| Performance regression | Medium | Medium | Performance budgets, monitoring |

### Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | Medium | High | Strict MVP focus, feature flags |
| Testing complexity | Medium | Medium | Start testing early, automation |
| Deployment issues | Low | High | Staging environment, rollback plan |

## Resource Requirements

### Team Allocation
- **Frontend Developer**: 100% (4 weeks)
- **DevOps Engineer**: 50% (4 weeks) - learning + implementation
- **QA Engineer**: 25% (weeks 3-4)
- **Backend Developer**: 10% (API support)

### Learning Resources
1. **React Fundamentals** (Week 1)
   - [React Official Tutorial](https://react.dev/learn)
   - [TypeScript for React](https://react-typescript-cheatsheet.netlify.app/)
   - Internal pair programming sessions

2. **Material-UI** (Week 2)
   - [MUI Getting Started](https://mui.com/material-ui/getting-started/)
   - Component examples in Storybook

3. **React Query** (Week 2)
   - [TanStack Query Docs](https://tanstack.com/query/latest)
   - Data fetching patterns guide

### Infrastructure
- Development environment (Docker)
- CI/CD pipeline (GitHub Actions)
- Staging environment (AWS S3 + CloudFront)
- Monitoring setup (Sentry, DataDog)

## Success Metrics

### Technical Metrics
- Bundle size: < 200KB gzipped
- Lighthouse score: > 90
- Test coverage: > 80%
- Build time: < 30s
- Deploy time: < 5min

### Developer Metrics
- Time to first component: < 1 day
- Time to implement feature: -30% vs HTMX
- Code reuse with mobile: > 40%
- Developer satisfaction: > 8/10

### User Metrics
- Page load time: < 3s
- Time to Interactive: < 5s
- Error rate: < 0.5%
- Feature parity: 100%

## Communication Plan

### Daily Updates
- Standup meetings at 10 AM
- Blockers escalated immediately
- Progress tracked in Jira

### Weekly Reviews
- Demo new features every Friday
- Retrospective on challenges
- Plan next week's work

### Stakeholder Communication
- Weekly status email
- Bi-weekly demo sessions
- Phase completion presentation

## Phase Completion Checklist

- [ ] React project setup with TypeScript
- [ ] Development environment configured
- [ ] CI/CD pipeline operational
- [ ] Authentication flow implemented
- [ ] Base routing and layouts complete
- [ ] Component library started (5+ components)
- [ ] API client integrated and tested
- [ ] State management patterns established
- [ ] Testing framework operational
- [ ] Performance baselines met
- [ ] Documentation complete
- [ ] Staging deployment successful
- [ ] Team trained on React basics
- [ ] Phase retrospective completed

## Next Steps

Upon successful completion of Phase 2:
1. Proceed to Phase 3: Core Feature Migration
2. Begin mobile/web code sharing setup
3. Plan user acceptance testing
4. Schedule gradual rollout strategy