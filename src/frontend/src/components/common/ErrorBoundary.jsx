import React, { Component } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { Error as ErrorIcon } from '@mui/icons-material';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '200px',
            p: 3,
            textAlign: 'center',
            backgroundColor: 'background.paper',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'error.main',
          }}
        >
          <ErrorIcon color="error" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Something went wrong
          </Typography>
          
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <Box sx={{ mt: 2, mb: 3, textAlign: 'left', width: '100%' }}>
              <Typography variant="body2" color="textSecondary">
                {this.state.error.toString()}
              </Typography>
              <pre style={{ overflowX: 'auto', fontSize: '12px', marginTop: '10px' }}>
                {this.state.errorInfo?.componentStack}
              </pre>
            </Box>
          )}
          
          <Button
            variant="contained"
            color="primary"
            onClick={this.handleRetry}
            sx={{ mt: 2 }}
          >
            Retry
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
