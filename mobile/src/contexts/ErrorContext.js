import React, { createContext, useContext, useState, useCallback } from 'react';
import { Alert } from 'react-native';

const ErrorContext = createContext();

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within ErrorProvider');
  }
  return context;
};

const ERROR_MESSAGES = {
  'Network request failed': 'No internet connection. Please check your network.',
  'Unauthorized': 'Session expired. Please login again.',
  'Forbidden': "You don't have permission to perform this action.",
  'Not Found': 'The requested item could not be found.',
  'Server Error': 'Something went wrong. Please try again later.',
  'Invalid credentials': 'Invalid username or password.',
  'User already exists': 'This username is already taken.',
  'Failed to fetch': 'Unable to connect to server. Please try again.',
  'Timeout': 'Request timed out. Please try again.',
};

export const ErrorProvider = ({ children }) => {
  const [errors, setErrors] = useState({});
  const [retryCallbacks, setRetryCallbacks] = useState({});

  const getErrorMessage = useCallback((error) => {
    // Check if error is an object with a message
    const errorString = error?.message || error?.detail || error?.toString() || 'Unknown error';
    
    // Check for known error patterns
    for (const [pattern, message] of Object.entries(ERROR_MESSAGES)) {
      if (errorString.toLowerCase().includes(pattern.toLowerCase())) {
        return message;
      }
    }
    
    // Default message
    return 'An unexpected error occurred. Please try again.';
  }, []);

  const showError = useCallback((error, options = {}) => {
    const { 
      key = 'default', 
      showAlert = true, 
      retryCallback = null,
      title = 'Error'
    } = options;

    const message = getErrorMessage(error);
    
    // Store error in state
    setErrors(prev => ({
      ...prev,
      [key]: { message, error }
    }));

    // Store retry callback if provided
    if (retryCallback) {
      setRetryCallbacks(prev => ({
        ...prev,
        [key]: retryCallback
      }));
    }

    // Show alert if requested
    if (showAlert) {
      const buttons = [{ text: 'OK', style: 'default' }];
      
      if (retryCallback) {
        buttons.unshift({
          text: 'Retry',
          onPress: () => {
            clearError(key);
            retryCallback();
          }
        });
      }

      Alert.alert(title, message, buttons);
    }

    return message;
  }, [getErrorMessage]);

  const clearError = useCallback((key = 'default') => {
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[key];
      return newErrors;
    });
    
    setRetryCallbacks(prev => {
      const newCallbacks = { ...prev };
      delete newCallbacks[key];
      return newCallbacks;
    });
  }, []);

  const retry = useCallback((key = 'default') => {
    const callback = retryCallbacks[key];
    if (callback) {
      clearError(key);
      callback();
    }
  }, [retryCallbacks, clearError]);

  const hasError = useCallback((key = 'default') => {
    return !!errors[key];
  }, [errors]);

  const getError = useCallback((key = 'default') => {
    return errors[key];
  }, [errors]);

  const value = {
    showError,
    clearError,
    retry,
    hasError,
    getError,
    getErrorMessage,
  };

  return (
    <ErrorContext.Provider value={value}>
      {children}
    </ErrorContext.Provider>
  );
};