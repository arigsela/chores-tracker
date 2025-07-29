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