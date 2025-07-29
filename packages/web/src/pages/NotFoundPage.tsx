import { Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
    >
      <Typography variant="h1" gutterBottom>
        404
      </Typography>
      <Typography variant="h5" color="text.secondary" gutterBottom>
        Page not found
      </Typography>
      <Button variant="contained" onClick={() => navigate('/')} sx={{ mt: 2 }}>
        Go to Dashboard
      </Button>
    </Box>
  )
}

export default NotFoundPage