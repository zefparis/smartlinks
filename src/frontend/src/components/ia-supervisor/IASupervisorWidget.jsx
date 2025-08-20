import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  TextField, 
  ToggleButton, 
  ToggleButtonGroup, 
  Tooltip, 
  Typography,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  useTheme
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
  Search,
  Send, 
  Settings, 
  Warning 
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useIASupervisor } from '../../hooks/useApi';
import ErrorBoundary from '../common/ErrorBoundary';
import { formatDistanceToNow } from 'date-fns';

const MODE_COLORS = {
  auto: 'success',
  manual: 'warning',
  sandbox: 'info',
};

const SEVERITY_ICONS = {
  info: <Info color="info" />,
  warning: <Warning color="warning" />,
  error: <ErrorIcon color="error" />,
  success: <CheckCircle color="success" />,
};

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[3],
  '&:hover': {
    boxShadow: theme.shadows[6],
  },
}));

const StyledCardHeader = styled(CardHeader)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  '& .MuiCardHeader-title': {
    fontWeight: 600,
  },
}));

const StyledCardContent = styled(CardContent)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
  padding: theme.spacing(2),
  '&::-webkit-scrollbar': {
    width: '6px',
  },
  '&::-webkit-scrollbar-track': {
    background: theme.palette.grey[200],
    borderRadius: '3px',
  },
  '&::-webkit-scrollbar-thumb': {
    background: theme.palette.primary.main,
    borderRadius: '3px',
  },
}));

const MessageBubble = styled(Box)(({ theme, isUser }) => ({
  maxWidth: '80%',
  padding: theme.spacing(1.5, 2),
  marginBottom: theme.spacing(1),
  borderRadius: theme.shape.borderRadius * 2,
  backgroundColor: isUser 
    ? theme.palette.primary.light 
    : theme.palette.grey[100],
  color: isUser 
    ? theme.palette.primary.contrastText 
    : theme.palette.text.primary,
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  '& pre': {
    backgroundColor: isUser 
      ? 'rgba(255, 255, 255, 0.1)' 
      : theme.palette.grey[200],
    padding: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    overflowX: 'auto',
  },
  '& code': {
    fontFamily: 'monospace',
    fontSize: '0.85rem',
  },
}));

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(0.5),
  textTransform: 'none',
  '& .MuiButton-startIcon': {
    marginRight: theme.spacing(0.5),
  },
}));

// MessageBubble component moved to the top level to avoid duplicate declaration

const SystemAlert = ({ alert, onDismiss }) => {
  const [open, setOpen] = useState(true);
  
  const handleClose = () => {
    setOpen(false);
    onDismiss?.(alert.id);
  };
  
  return (
    <Collapse in={open}>
      <Alert 
        severity={alert.severity}
        sx={{ mb: 2 }}
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={handleClose}
          >
            <Close fontSize="inherit" />
          </IconButton>
        }
      >
        <Typography variant="subtitle2">{alert.title}</Typography>
        <Typography variant="body2">{alert.message}</Typography>
        {alert.details && (
          <Box sx={{ mt: 1 }}>
            <Button 
              size="small" 
              onClick={() => setOpen(!open)}
              endIcon={open ? <ExpandLess /> : <ExpandMore />}
            >
              {open ? 'Hide details' : 'Show details'}
            </Button>
            <Collapse in={open} timeout="auto" unmountOnExit>
              <pre style={{ 
                whiteSpace: 'pre-wrap',
                fontSize: '0.8em',
                margin: '8px 0 0',
                padding: '8px',
                backgroundColor: 'rgba(0,0,0,0.05)',
                borderRadius: '4px',
                maxHeight: '200px',
                overflowY: 'auto',
              }}>
                {JSON.stringify(alert.details, null, 2)}
              </pre>
            </Collapse>
          </Box>
        )}
      </Alert>
    </Collapse>
  );
};

const IASupervisorWidget = () => {
  const theme = useTheme();
  
  // State
  const [inputValue, setInputValue] = useState('');
  const [openSettings, setOpenSettings] = useState(false);
  const [localAlerts, setLocalAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info',
  });
  
  // Use the enhanced hook
  const {
    status,
    alerts: apiAlerts,
    logs,
    loading,
    error,
    askQuestion,
    analyzeSystem,
    fixIssues,
    switchMode,
    fetchStatus,
  } = useIASupervisor();
  
  // Combine local and API alerts
  const allAlerts = useMemo(() => {
    return [...localAlerts, ...apiAlerts];
  }, [localAlerts, apiAlerts]);
  
  // Process logs into message format
  const messages = useMemo(() => {
    return logs.map(log => ({
      id: log.id || log.timestamp,
      text: log.content || log.message || JSON.stringify(log),
      isUser: log.type === 'question' || log.role === 'user',
      timestamp: log.timestamp || new Date().toISOString(),
      severity: log.severity || 'info',
    }));
  }, [logs]);
  
  // Current mode from status or default to 'auto'
  const mode = status?.mode || 'auto';

  // Handle sending a message
  const handleSendMessage = useCallback(async (message) => {
    if (!message?.trim()) return;
    
    setIsLoading(true);
    
    const userMessage = {
      id: `user-${Date.now()}`,
      text: message,
      isUser: true,
      timestamp: new Date().toISOString(),
    };
    
    try {
      setInputValue('');
      
      // Show typing indicator
      const typingIndicator = {
        id: `typing-${Date.now()}`,
        text: '...',
        isUser: false,
        isLoading: true,
        timestamp: new Date().toISOString(),
      };
      
      // Add user message and typing indicator to logs
      setLogs(prev => [...prev, userMessage, typingIndicator]);
      
      // Send message to the API
      const response = await askQuestion(message);
      
      // Remove typing indicator
      setLogs(prev => prev.filter(log => log.id !== typingIndicator.id));
      
      // Add bot response if available
      if (response) {
        setLogs(prev => [...prev, {
          id: `bot-${Date.now()}`,
          text: response,
          isUser: false,
          timestamp: new Date().toISOString(),
        }]);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove typing indicator on error
      setLogs(prev => prev.filter(log => log.isLoading !== true));
      setIsLoading(false);
      
      // Show error message
      setLocalAlerts(prev => [{
        id: `error-${Date.now()}`,
        title: 'Error',
        message: 'Failed to send message',
        details: error.message,
        severity: 'error',
        timestamp: new Date().toISOString(),
      }, ...prev]);
    }
  }, [askQuestion]);

  // Fetch initial status and set up the component
  useEffect(() => {
    const init = async () => {
      try {
        await fetchStatus();
        
        // Add welcome message if no logs exist
        if (logs.length === 0) {
          setLocalAlerts(prev => [{
            id: 'welcome-alert',
            title: 'Welcome to AI Supervisor',
            message: 'The AI Supervisor is now active and monitoring your system.',
            severity: 'info',
            timestamp: new Date().toISOString(),
          }, ...prev]);
        }
      } catch (err) {
        console.error('Failed to initialize:', err);
        setLocalAlerts(prev => [{
          id: `init-error-${Date.now()}`,
          title: 'Initialization Error',
          message: 'Failed to initialize AI Supervisor',
          details: err.message,
          severity: 'error',
          timestamp: new Date().toISOString(),
        }, ...prev]);
      }
    };
    
    init();
    
    // Set up keyboard shortcuts
    const handleKeyDown = (e) => {
      // Focus the input when pressing / (but not when typing in an input)
      if (e.key === '/' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('ai-chat-input')?.focus();
      }
      
      // Send message with Cmd+Enter or Ctrl+Enter
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && inputValue.trim()) {
        e.preventDefault();
        handleSendMessage(inputValue);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [fetchStatus, logs.length, handleSendMessage, inputValue]);

  // Add a bot message to the chat and update alerts
  const addBotMessage = useCallback((text, severity = 'info') => {
    const botMessage = {
      id: `bot-${Date.now()}`,
      text,
      isUser: false,
      severity,
      timestamp: new Date().toISOString(),
    };
    
    setLocalAlerts(prev => [{
      id: `message-${Date.now()}`,
      title: 'New Message',
      message: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
      details: { text, severity },
      severity,
      timestamp: new Date().toISOString(),
    }, ...prev]);
    
    return botMessage;
  }, []);
  
  // Dismiss an alert
  const handleDismissAlert = useCallback((alertId) => {
    setLocalAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);
  
  // Format the last updated time
  const lastUpdated = useMemo(() => {
    if (!status?.lastUpdated) return 'Never';
    
    try {
      return formatDistanceToNow(new Date(status.lastUpdated), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  }, [status?.lastUpdated]);

  // Handle mode change
  const handleModeChange = async (event, newMode) => {
    if (newMode === null || newMode === mode) return;
    
    try {
      await switchMode(newMode);
      
      setLocalAlerts(prev => [{
        id: `mode-change-${Date.now()}`,
        title: 'Mode Changed',
        message: `Switched to ${newMode} mode`,
        severity: 'success',
        timestamp: new Date().toISOString(),
      }, ...prev]);
      
      // Show confirmation message in chat
      addBotMessage(
        `Operation mode changed to **${newMode}**. ` +
        (newMode === 'auto' 
          ? 'I will now automatically manage the system.' 
          : newMode === 'manual' 
            ? 'I will require approval for all actions.'
            : 'Running in sandbox mode. No changes will be made to the system.')
      );
      
      // Refresh the status to reflect the new mode
      await fetchStatus();
    } catch (err) {
      console.error('Error changing mode:', err);
      
      setLocalAlerts(prev => [{
        id: `mode-error-${Date.now()}`,
        title: 'Error',
        message: 'Failed to change operation mode',
        details: err.message,
        severity: 'error',
        timestamp: new Date().toISOString(),
      }, ...prev]);
    }
  };

  // Analyze the system
  const handleAnalyze = async () => {
    try {
      addBotMessage('Analyzing system status...', 'info');
      
      const result = await analyzeSystem();
      
      // Format the analysis result
      const summary = result.summary || 'Analysis completed';
      const findings = result.keyFindings || [];
      const recommendations = result.recommendations || [];
      
      let message = `### ${summary}\n\n`;
      
      if (findings.length > 0) {
        message += '**Key Findings:**\n';
        findings.forEach((finding, index) => {
          message += `${index + 1}. ${finding}\n`;
        });
      }
      
      if (recommendations.length > 0) {
        message += '\n**Recommendations:**\n';
        recommendations.forEach((rec, index) => {
          message += `${index + 1}. ${rec}\n`;
        });
      }
      
      addBotMessage(message, 'info');
      
      setLocalAlerts(prev => [{
        id: `analysis-${Date.now()}`,
        title: 'Analysis Complete',
        message: summary,
        details: { findings, recommendations },
        severity: 'success',
        timestamp: new Date().toISOString(),
      }, ...prev]);
    } catch (error) {
      console.error('Error analyzing system:', error);
      showSnackbar('Failed to analyze system', 'error');
      addBotMessage('Failed to analyze system. Please check the logs for details.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Fix detected issues
  const handleFixIssues = async () => {
    try {
      addBotMessage('Attempting to fix detected issues...', 'info');
      
      const result = await fixIssues();
      
      if (result.actionsExecuted > 0) {
        const message = `Successfully executed ${result.actionsExecuted} action${result.actionsExecuted !== 1 ? 's' : ''} to fix issues.`;
        
        addBotMessage(message, 'success');
        
        setLocalAlerts(prev => [{
          id: `fix-success-${Date.now()}`,
          title: 'Issues Fixed',
          message: message,
          details: result,
          severity: 'success',
          timestamp: new Date().toISOString(),
        }, ...prev]);
      } else {
        const message = 'No issues requiring fixes were found.';
        addBotMessage(message, 'info');
        
        setLocalAlerts(prev => [{
          id: `fix-info-${Date.now()}`,
          title: 'No Fixes Needed',
          message: message,
          severity: 'info',
          timestamp: new Date().toISOString(),
        }, ...prev]);
      }
      
      // Refresh status after fixes
      await fetchStatus();
    } catch (err) {
      console.error('Error fixing issues:', err);
      
      const errorMessage = 'Failed to fix issues. Please check the logs for details.';
      addBotMessage(errorMessage, 'error');
      
      setLocalAlerts(prev => [{
        id: `fix-error-${Date.now()}`,
        title: 'Fix Failed',
        message: errorMessage,
        details: err.message,
        severity: 'error',
        timestamp: new Date().toISOString(),
      }, ...prev]);
    }
  };

  // Show a snackbar notification
  const showSnackbar = useCallback((message, severity = 'info') => {
    setSnackbar({
      open: true,
      message,
      severity,
    });
  }, []);

  // Close the snackbar
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Render a message with markdown support
  const renderMessage = (text) => {
    if (!text) return null;
    
    // Simple markdown parsing (for demonstration)
    const parts = [];
    
    // Process bold text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let lastIndex = 0;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={lastIndex}>{text.substring(lastIndex, match.index)}</span>);
      }
      parts.push(<strong key={`bold-${match.index}`}>{match[1]}</strong>);
      lastIndex = match.index + match[0].length;
    }
    
    if (lastIndex < text.length) {
      parts.push(<span key={lastIndex}>{text.substring(lastIndex)}</span>);
    }
    
    // Handle line breaks
    const result = [];
    parts.forEach((part, i) => {
      if (typeof part === 'string') {
        const lines = part.split('\n');
        lines.forEach((line, j) => {
          if (j > 0) result.push(<br key={`br-${i}-${j}`} />);
          result.push(<span key={`${i}-${j}`}>{line}</span>);
        });
      } else {
        result.push(part);
      }
    });
    
    return <>{result}</>;
  };

  return (
    <ErrorBoundary>
      <StyledCard elevation={3}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center">
                <AutoFixHigh sx={{ mr: 1 }} />
                <Typography variant="h6">AI Supervisor</Typography>
              </Box>
              <Box>
                <Chip 
                  label={mode ? mode.toUpperCase() : 'N/A'}
                  color={mode ? (MODE_COLORS[mode] || 'default') : 'default'}
                  size="small"
                  sx={{ mr: 1, color: 'white', fontWeight: 'bold' }}
                />
                <Tooltip title="Settings">
                  <IconButton 
                    size="small" 
                    sx={{ ml: 1, color: 'white' }}
                    onClick={() => setOpenSettings(true)}
                  >
                    <Settings />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Refresh">
                  <IconButton 
                    size="small" 
                    sx={{ ml: 0.5, color: 'white' }}
                    onClick={fetchStatus}
                    disabled={isLoading}
                  >
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          }
        />
        
        <CardContent>
          {/* System Alerts */}
          {allAlerts.slice(0, 3).map(alert => (
            <SystemAlert 
              key={alert.id} 
              alert={alert} 
              onDismiss={handleDismissAlert}
            />
          ))}
          
          {/* Chat Messages */}
          <Box 
            sx={{ 
              flexGrow: 1, 
              mb: 2,
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto',
              minHeight: '200px',
              maxHeight: '400px',
              p: 1,
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
                textAlign="center"
                p={2}
              >
                <Help sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="body2">
                  Ask me anything about the SmartLinks DG system or request an analysis.
                </Typography>
              </Box>
            ) : (
              messages.map((message) => (
                <MessageBubble 
                  key={message.id} 
                  isUser={message.isUser}
                  sx={{
                    mb: 1,
                    opacity: isLoading && message.id === messages[messages.length - 1]?.id ? 0.7 : 1,
                  }}
                >
                  {renderMessage(message.text)}
                  <Typography 
                    variant="caption" 
                    display="block" 
                    textAlign="right"
                    sx={{ 
                      mt: 0.5, 
                      opacity: 0.7,
                      color: message.isUser ? 'rgba(255, 255, 255, 0.7)' : 'inherit',
                    }}
                  >
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Typography>
                </MessageBubble>
              ))
            )}
            
            {isLoading && messages.length > 0 && (
              <Box display="flex" justifyContent="center" my={1}>
                <CircularProgress size={20} />
              </Box>
            )}
          </Box>
          
          {/* Quick actions */}
          <Box display="flex" flexWrap="wrap" mb={2}>
            <ActionButton
              variant="outlined"
              size="small"
              startIcon={<BugReport />}
              onClick={handleAnalyze}
              disabled={isLoading}
            >
              Analyze System
            </ActionButton>
            
            <ActionButton
              variant="outlined"
              color="secondary"
              size="small"
              startIcon={<AutoFixHigh />}
              onClick={handleFixIssues}
              disabled={isLoading || mode === 'manual'}
              title={mode === 'manual' ? 'Switch to auto mode to fix issues' : ''}
            >
              Fix Issues
            </ActionButton>
          </Box>
          
          {/* Input area */}
          <Box display="flex" mt="auto">
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              placeholder="Ask me anything..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (inputValue.trim()) {
                    handleSendMessage(inputValue);
                  }
                }
              }}
              disabled={isLoading}
              multiline
              maxRows={4}
              InputProps={{
                endAdornment: (
                  <IconButton 
                    onClick={() => inputValue.trim() && handleSendMessage(inputValue)}
                    disabled={loading || !inputValue.trim()}
                    color="primary"
                    edge="end"
                  >
                    <Send />
                  </IconButton>
                ),
              }}
            />
          </Box>
          
          {/* Status Bar */}
          <Box mt={1} display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="textSecondary">
              Last updated: {lastUpdated}
            </Typography>
            <Box display="flex" alignItems="center">
              {status?.version && (
                <Chip 
                  label={`v${status.version}`} 
                  size="small" 
                  variant="outlined"
                  sx={{ mr: 1 }}
                />
              )}
              <Chip 
                icon={status?.isConnected ? <CheckCircle fontSize="small" /> : <ErrorIcon fontSize="small" />}
                label={status?.isConnected ? 'Connected' : 'Disconnected'}
                color={status?.isConnected ? 'success' : 'error'}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        </CardContent>
        
        {/* Settings Dialog */}
        <Dialog 
          open={openSettings} 
          onClose={() => setOpenSettings(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>AI Supervisor Settings</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Configure the AI Supervisor behavior and preferences.
            </DialogContentText>
            
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                Operation Mode
              </Typography>
              <ToggleButtonGroup
                value={mode}
                exclusive
                onChange={handleModeChange}
                fullWidth
                aria-label="operation mode"
                disabled={loading}
              >
                <ToggleButton value="auto" aria-label="auto mode">
                  <Box textAlign="center" p={1}>
                    <AutoFixHigh sx={{ mb: 0.5 }} />
                    <Typography variant="caption" display="block">Auto</Typography>
                    <Typography variant="caption" color="textSecondary" display="block">AI takes actions automatically</Typography>
                  </Box>
                </ToggleButton>
                <ToggleButton value="manual" aria-label="manual mode">
                  <Box textAlign="center" p={1}>
                    <Settings sx={{ mb: 0.5 }} />
                    <Typography variant="caption" display="block">Manual</Typography>
                    <Typography variant="caption" color="textSecondary" display="block">Requires approval</Typography>
                  </Box>
                </ToggleButton>
                <ToggleButton value="sandbox" aria-label="sandbox mode">
                  <Box textAlign="center" p={1}>
                    <BugReport sx={{ mb: 0.5 }} />
                    <Typography variant="caption" display="block">Sandbox</Typography>
                    <Typography variant="caption" color="textSecondary" display="block">Simulation only</Typography>
                  </Box>
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>
            
            <Box mt={3}>
              <Typography variant="subtitle2" gutterBottom>
                System Status
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Last Updated" 
                    secondary={lastUpdated} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Active Algorithms" 
                    secondary={status?.algorithms?.length || 0} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Issues Detected" 
                    secondary={status?.issues?.length || 0} 
                  />
                </ListItem>
              </List>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenSettings(false)}>Close</Button>
          </DialogActions>
        </Dialog>
        
        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        >
          <Alert 
            onClose={handleCloseSnackbar} 
            severity={snackbar.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </StyledCard>
    </ErrorBoundary>
  );
};

export default IASupervisorWidget;
