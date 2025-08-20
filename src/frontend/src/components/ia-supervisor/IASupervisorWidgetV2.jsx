import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Snackbar,
  TextField,
  Typography,
  Alert as MuiAlert,
  styled,
} from '@mui/material';
import {
  AutoFixHigh,
  BugReport,
  CheckCircle,
  Close,
  Error as ErrorIcon,
  ExpandLess,
  ExpandMore,
  Help,
  Info,
  Refresh,
  Settings,
  Warning,
} from '@mui/icons-material';
import useIASupervisor from '../../hooks/useIASupervisorV2';
import { ApiErrorType } from '../../hooks/useApiV2';
import { chatWithOpenAI } from '../../lib/openai';

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  maxWidth: 600,
  margin: '0 auto',
  boxShadow: theme.shadows[3],
  borderRadius: theme.shape.borderRadius,
  '& .MuiCardHeader-root': {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    '& .MuiCardHeader-action': {
      margin: 0,
    },
  },
}));

const MessageBubble = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})(({ isUser, theme }) => ({
  maxWidth: '80%',
  padding: theme.spacing(1.5, 2),
  margin: theme.spacing(0.5, 0),
  borderRadius: 18,
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[200],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  wordBreak: 'break-word',
}));

const IASupervisorWidget = () => {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const messagesEndRef = React.useRef(null);

  const {
    isAvailable,
    status,
    loading: apiLoading,
    error: apiError,
    askQuestion,
    analyzeSystem,
    checkAvailability,
    refresh,
  } = useIASupervisor();

  // Removed stressful unavailable messages - we have fallback now

  // Surface non-aborted  // Show error if API error occurs (simplified)
  useEffect(() => {
    if (!apiError) return;
    
    // Don't show error messages for unavailable service - we have fallback
    if (apiError?.type === ApiErrorType.NOT_FOUND) return;

    const friendly =
      apiError?.type === ApiErrorType.NETWORK
        ? 'Problème de connexion réseau.'
        : apiError?.type === ApiErrorType.TIMEOUT
          ? 'Délai d\'attente dépassé.'
          : 'Une erreur s\'est produite.';

    setSnackbar({ open: true, message: friendly, severity: 'warning' });
  }, [apiError]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // Try backend first, fallback to direct OpenAI
      let response;
      if (isAvailable) {
        try {
          response = await askQuestion(currentInput);
        } catch (backendError) {
          console.warn('Backend IA failed, trying direct OpenAI:', backendError);
          response = await chatWithOpenAI(currentInput);
        }
      } else {
        // Backend unavailable, use direct OpenAI
        response = await chatWithOpenAI(currentInput);
      }
      
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          text: response || 'Désolé, je ne peux pas traiter votre demande pour le moment.',
          isUser: false,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      // Ignore cancelled requests and don't show error messages - we have fallback
      if (error?.type === ApiErrorType.ABORTED) return;
      
      // Only show critical errors, not service unavailable ones
      if (error?.type !== ApiErrorType.NOT_FOUND) {
        const friendly =
          error?.type === ApiErrorType.NETWORK
            ? 'Problème de connexion'
            : error?.type === ApiErrorType.TIMEOUT
              ? 'Délai dépassé'
              : 'Erreur temporaire';

        setSnackbar({
          open: true,
          message: friendly,
          severity: 'warning',
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isAvailable, askQuestion]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      await refresh();
      setSnackbar({
        open: true,
        message: 'Refreshed IA Supervisor data',
        severity: 'success',
      });
    } catch (error) {
      if (error?.type !== ApiErrorType.ABORTED) {
        const friendly =
          error?.type === ApiErrorType.NOT_FOUND
            ? 'IA service is not available.'
            : error?.type === ApiErrorType.NETWORK
              ? 'Network error while refreshing.'
              : error?.type === ApiErrorType.TIMEOUT
                ? 'Refresh timed out. Try again.'
                : 'Failed to refresh data';
        setSnackbar({ open: true, message: friendly, severity: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  if (apiLoading && !isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <StyledCard>
      <CardHeader
        title="IA Supervisor"
        action={
          <>
            <IconButton 
              aria-label="refresh" 
              onClick={handleRefresh}
              disabled={isLoading}
              color="inherit"
            >
              <Refresh />
            </IconButton>
            <Chip
              label={isAvailable ? 'Online' : 'Offline'}
              color={isAvailable ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
          </>
        }
      />
      <CardContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {status?.message || 'Ask me anything about the system'}
          </Typography>
        </Box>

        <Box
          sx={{
            height: 300,
            overflowY: 'auto',
            mb: 2,
            p: 1,
            bgcolor: 'background.paper',
            borderRadius: 1,
          }}
        >
          {messages.length === 0 ? (
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              height="100%"
              color="text.secondary"
            >
              <Help sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
              <Typography variant="body2">
                Démarrez une conversation avec l'assistant IA
              </Typography>
            </Box>
          ) : (
            <Box display="flex" flexDirection="column">
              {messages.map((message) => (
                <MessageBubble key={message.id} isUser={message.isUser}>
                  <Typography variant="body1">{message.text}</Typography>
                  <Typography variant="caption" display="block" textAlign="right" sx={{ opacity: 0.7, mt: 0.5 }}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Typography>
                </MessageBubble>
              ))}
              <div ref={messagesEndRef} />
            </Box>
          )}
        </Box>

        <Box display="flex" alignItems="center">
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Tapez votre message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            size="small"
            sx={{ mr: 1 }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
          >
            {isLoading ? <CircularProgress size={24} /> : 'Send'}
          </Button>
        </Box>
      </CardContent>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <MuiAlert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
          elevation={6}
          variant="filled"
        >
          {snackbar.message}
        </MuiAlert>
      </Snackbar>
    </StyledCard>
  );
};

export default IASupervisorWidget;
