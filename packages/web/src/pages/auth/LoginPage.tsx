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
import { useAuth } from '@/hooks/useAuth'

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