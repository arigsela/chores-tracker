import { Typography, Box } from '@mui/material'
import { useAuth } from '@/hooks/useAuth'

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.full_name}!
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Dashboard content will be implemented here.
      </Typography>
    </Box>
  )
}

export default DashboardPage