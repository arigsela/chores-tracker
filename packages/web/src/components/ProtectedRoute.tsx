import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
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