/**
 * Chores Tracker App
 * @format
 */

import React from 'react';
import { StatusBar, useColorScheme } from 'react-native';
import { AuthProvider } from './src/store/authContext';
import AppNavigator from './src/navigation/AppNavigator';

function App() {
  const isDarkMode = useColorScheme() === 'dark';

  return (
    <AuthProvider>
      <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
      <AppNavigator />
    </AuthProvider>
  );
}

export default App;
