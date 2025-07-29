import { Typography, Box } from '@mui/material'

export const UsersPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Users
      </Typography>
      <Typography variant="body1" color="text.secondary">
        User management will be implemented here.
      </Typography>
    </Box>
  )
}

export default UsersPage