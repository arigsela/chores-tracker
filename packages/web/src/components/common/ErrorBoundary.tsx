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