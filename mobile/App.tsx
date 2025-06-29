/**
 * Chores Tracker App
 * @format
 */

import React from 'react';
import { StatusBar, useColorScheme } from 'react-native';
import { AuthProvider } from './src/store/authContext';
import { ErrorProvider } from './src/contexts/ErrorContext';
import { ToastProvider } from './src/contexts/ToastContext';
import ErrorBoundary from './src/components/common/ErrorBoundary';
import NetworkStatusBar from './src/components/common/NetworkStatusBar';
import AppNavigator from './src/navigation/AppNavigator';

function App() {
  const isDarkMode = useColorScheme() === 'dark';

  return (
    <ErrorBoundary>
      <ErrorProvider>
        <ToastProvider>
          <AuthProvider>
            <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
            <NetworkStatusBar />
            <AppNavigator />
          </AuthProvider>
        </ToastProvider>
      </ErrorProvider>
    </ErrorBoundary>
  );
}

export default App;
