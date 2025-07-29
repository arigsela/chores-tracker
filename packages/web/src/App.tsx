import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { SnackbarProvider } from 'notistack'
import { AuthProvider } from '@/contexts/AuthContext'
import { theme } from '@/styles/theme'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { MainLayout } from '@/layouts/MainLayout'

// Pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ChoresPage } from '@/pages/chores/ChoresPage'
import { CreateChorePage } from '@/pages/chores/CreateChorePage'
import { UsersPage } from '@/pages/users/UsersPage'
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
        <SnackbarProvider maxSnack={3}>
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
        </SnackbarProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
