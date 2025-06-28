# React Native Implementation Guide - Chores Tracker

This document serves as the living implementation guide for the Chores Tracker React Native mobile app. It tracks our progress, decisions, and provides detailed implementation steps.

## Implementation Status

### Current Phase: **Phase 1 - Core Infrastructure and Authentication** 🚀

### Completed Phases: 
- ✅ **Phase 0 - Project Setup** (December 28, 2024)
  - [x] Development environment configured
  - [x] React Native project initialized
  - [x] Basic project structure created
  - [x] Connected to physical iPhone for testing
  - [x] All dependencies installed
  - [x] iOS build configuration completed
  - [x] Successfully running on physical device

---

## Phase 0: Project Setup and Environment Configuration

### 0.1 Prerequisites Installation

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js (v18 or later recommended)
brew install node

# Install Watchman (Facebook's file watcher for hot reload)
brew install watchman

# Install CocoaPods (iOS dependency manager)
sudo gem install cocoapods

# Install React Native CLI globally
npm install -g react-native-cli
```

### 0.2 Xcode Setup
1. Install Xcode from Mac App Store (this takes a while, ~7GB)
2. Open Xcode and agree to license
3. Install additional components when prompted
4. Ensure Command Line Tools are installed:
   ```bash
   xcode-select --install
   ```

### 0.3 Create React Native Project

```bash
# Navigate to your chores-tracker directory
cd /Users/arisela/git/chores-tracker

# Create React Native project in mobile folder
npx react-native@latest init ChoresTrackerMobile --directory mobile

# Navigate to the mobile directory
cd mobile
```

### 0.4 Project Structure Setup

Create the following directory structure:

```
mobile/
├── src/
│   ├── api/
│   │   ├── client.js
│   │   ├── endpoints.js
│   │   └── index.js
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.js
│   │   │   ├── Input.js
│   │   │   └── LoadingSpinner.js
│   │   └── chores/
│   │       ├── ChoreCard.js
│   │       └── ChoreList.js
│   ├── navigation/
│   │   ├── AppNavigator.js
│   │   ├── AuthNavigator.js
│   │   └── MainNavigator.js
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── LoginScreen.js
│   │   │   └── SplashScreen.js
│   │   ├── parent/
│   │   │   ├── ParentHomeScreen.js
│   │   │   ├── CreateChoreScreen.js
│   │   │   └── ApprovalScreen.js
│   │   └── child/
│   │       ├── ChildHomeScreen.js
│   │       └── ChoreDetailScreen.js
│   ├── services/
│   │   ├── authService.js
│   │   ├── choreService.js
│   │   └── storageService.js
│   ├── store/
│   │   ├── authContext.js
│   │   └── choreContext.js
│   ├── utils/
│   │   ├── constants.js
│   │   ├── helpers.js
│   │   └── validators.js
│   └── styles/
│       ├── colors.js
│       ├── typography.js
│       └── common.js
├── App.js
├── package.json
└── ios/
```

### 0.5 Install Core Dependencies

```bash
# Navigation
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context

# UI Components
npm install react-native-elements react-native-vector-icons
npm install react-native-gesture-handler react-native-reanimated

# API and Storage
npm install axios
npm install @react-native-async-storage/async-storage

# Utilities
npm install react-native-keyboard-aware-scroll-view
npm install date-fns
npm install react-native-config  # For environment variables

# Biometrics (Face ID)
npm install react-native-biometrics

# iOS specific setup
cd ios && pod install && cd ..
```

### 0.6 Configure iOS Project

1. Open `ios/ChoresTrackerMobile.xcworkspace` in Xcode
2. Select your project in navigator
3. Under "Signing & Capabilities":
   - Select your Apple ID team
   - Change bundle identifier to something unique: `com.yourname.chorestracker`
4. Add Face ID permission to `ios/ChoresTrackerMobile/Info.plist`:
   ```xml
   <key>NSFaceIDUsageDescription</key>
   <string>Use Face ID to secure your chores data</string>
   ```

### 0.7 Environment Configuration

Create `.env.development`:
```
API_URL=http://localhost:8000/api/v1
```

Create `.env.production`:
```
API_URL=https://api.chorestracker.com/api/v1
```

### 0.8 Test Basic Setup

```bash
# Start Metro bundler
npm start

# In another terminal, run on iOS
npm run ios

# Or to run on your physical device:
# 1. Connect iPhone via USB
# 2. Trust computer on iPhone
# 3. In Xcode, select your iPhone as target device
# 4. Click Run button
```

---

## Phase 1: Core Infrastructure and Authentication 🔒

### 1.1 API Client Setup

**File: `src/api/client.js`**
```javascript
import axios from 'axios';
import Config from 'react-native-config';
import { storageService } from '../services/storageService';

const API_URL = Config.API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await storageService.getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await storageService.clearAll();
      // Navigate to login (will be handled by auth context)
    }
    console.error('Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 1.2 Storage Service

**File: `src/services/storageService.js`**
```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  AUTH_TOKEN: '@ChoresTracker:authToken',
  USER_DATA: '@ChoresTracker:userData',
  BIOMETRIC_ENABLED: '@ChoresTracker:biometricEnabled',
};

export const storageService = {
  // Auth Token
  async setAuthToken(token) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    } catch (error) {
      console.error('Error saving auth token:', error);
    }
  },

  async getAuthToken() {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  },

  // User Data
  async setUserData(userData) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
    } catch (error) {
      console.error('Error saving user data:', error);
    }
  },

  async getUserData() {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.USER_DATA);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting user data:', error);
      return null;
    }
  },

  // Biometric Settings
  async setBiometricEnabled(enabled) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, JSON.stringify(enabled));
    } catch (error) {
      console.error('Error saving biometric setting:', error);
    }
  },

  async getBiometricEnabled() {
    try {
      const enabled = await AsyncStorage.getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
      return enabled ? JSON.parse(enabled) : false;
    } catch (error) {
      console.error('Error getting biometric setting:', error);
      return false;
    }
  },

  // Clear All
  async clearAll() {
    try {
      await AsyncStorage.multiRemove(Object.values(STORAGE_KEYS));
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },
};
```

### 1.3 Authentication Service

**File: `src/services/authService.js`**
```javascript
import apiClient from '../api/client';
import { storageService } from './storageService';
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';

const rnBiometrics = new ReactNativeBiometrics();

export const authService = {
  async login(username, password) {
    try {
      // Form data for OAuth2 password flow
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');

      const response = await apiClient.post('/auth/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, token_type } = response.data;

      // Store token
      await storageService.setAuthToken(access_token);

      // Get user profile
      const userResponse = await apiClient.get('/users/me');
      await storageService.setUserData(userResponse.data);

      return {
        success: true,
        user: userResponse.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  },

  async logout() {
    try {
      // Clear local storage
      await storageService.clearAll();
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  },

  async checkBiometricAvailability() {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      
      if (available && biometryType === BiometryTypes.FaceID) {
        return { available: true, type: 'FaceID' };
      } else if (available && biometryType === BiometryTypes.TouchID) {
        return { available: true, type: 'TouchID' };
      } else if (available && biometryType === BiometryTypes.Biometrics) {
        return { available: true, type: 'Biometrics' };
      } else {
        return { available: false, type: null };
      }
    } catch (error) {
      console.error('Biometric check error:', error);
      return { available: false, type: null };
    }
  },

  async authenticateWithBiometric() {
    try {
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage: 'Authenticate to access Chores Tracker',
        cancelButtonText: 'Cancel',
      });
      return success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  },

  async setupBiometric() {
    const biometricEnabled = await storageService.getBiometricEnabled();
    if (!biometricEnabled) {
      const { available } = await this.checkBiometricAvailability();
      if (available) {
        await storageService.setBiometricEnabled(true);
        return true;
      }
    }
    return biometricEnabled;
  },

  async getCurrentUser() {
    return await storageService.getUserData();
  },

  async isAuthenticated() {
    const token = await storageService.getAuthToken();
    const user = await storageService.getUserData();
    return !!(token && user);
  },
};
```

### 1.4 Auth Context

**File: `src/store/authContext.js`**
```javascript
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthState();
  }, []);

  const checkAuthState = async () => {
    try {
      const authenticated = await authService.isAuthenticated();
      if (authenticated) {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Auth state check error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username, password) => {
    const result = await authService.login(username, password);
    if (result.success) {
      setUser(result.user);
      setIsAuthenticated(true);
    }
    return result;
  };

  const logout = async () => {
    const result = await authService.logout();
    if (result.success) {
      setUser(null);
      setIsAuthenticated(false);
    }
    return result;
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    isParent: user?.role === 'parent',
    isChild: user?.role === 'child',
    login,
    logout,
    checkAuthState,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

### 1.5 Login Screen

**File: `src/screens/auth/LoginScreen.js`**
```javascript
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../store/authContext';
import { authService } from '../../services/authService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const LoginScreen = ({ navigation }) => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);

  useEffect(() => {
    checkBiometric();
  }, []);

  const checkBiometric = async () => {
    const { available } = await authService.checkBiometricAvailability();
    setBiometricAvailable(available);
  };

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter username and password');
      return;
    }

    setIsLoading(true);
    try {
      const result = await login(username, password);
      if (!result.success) {
        Alert.alert('Login Failed', result.error);
      }
      // Navigation will be handled by auth state change
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    const success = await authService.authenticateWithBiometric();
    if (success) {
      // Check if we have stored credentials
      const user = await authService.getCurrentUser();
      if (user) {
        // Already logged in, just needed biometric verification
        navigation.navigate('Main');
      } else {
        Alert.alert('Info', 'Please login with username and password first');
      }
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Chores Tracker</Text>
          <Text style={styles.subtitle}>Login to continue</Text>
        </View>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Username"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!isLoading}
          />

          <TextInput
            style={styles.input}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            editable={!isLoading}
          />

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.buttonText}>Login</Text>
            )}
          </TouchableOpacity>

          {biometricAvailable && (
            <TouchableOpacity
              style={styles.biometricButton}
              onPress={handleBiometricLogin}
            >
              <Text style={styles.biometricButtonText}>Login with Face ID</Text>
            </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    ...typography.h1,
    color: colors.primary,
    marginBottom: 8,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
  },
  form: {
    width: '100%',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 16,
    marginBottom: 16,
    fontSize: 16,
    backgroundColor: 'white',
  },
  button: {
    height: 50,
    backgroundColor: colors.primary,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  biometricButton: {
    height: 50,
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  biometricButtonText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default LoginScreen;
```

---

## Phase 2: Navigation and Core Screens 🧭

### 2.1 Navigation Structure
- [ ] App Navigator (handles auth state)
- [ ] Auth Stack (Login, Register)
- [ ] Main Tab Navigator
  - [ ] Parent Stack (Home, Create Chore, Approvals)
  - [ ] Child Stack (Home, Chore Details)
- [ ] Role-based navigation

### 2.2 Parent Screens
- [ ] Parent Home (list of all family chores)
- [ ] Create/Edit Chore
- [ ] Approval Queue
- [ ] Child Management

### 2.3 Child Screens
- [ ] Child Home (assigned chores)
- [ ] Chore Detail/Complete
- [ ] Rewards Summary

---

## Phase 3: Chore Management Features 📋

### 3.1 Chore CRUD Operations
- [ ] Create chore (parent)
- [ ] Edit chore (parent)
- [ ] Delete/disable chore (parent)
- [ ] List chores with filters

### 3.2 Chore Completion Flow
- [ ] Mark chore as complete (child)
- [ ] Upload proof photo (optional)
- [ ] Submit for approval

### 3.3 Approval System
- [ ] Approval notifications
- [ ] Approve/reject with feedback
- [ ] Reward assignment

---

## Phase 4: Advanced Features 🚀

### 4.1 Recurring Chores
- [ ] Handle recurrence patterns
- [ ] Cooldown periods
- [ ] Next instance generation

### 4.2 Notifications
- [ ] Push notification setup
- [ ] Chore reminders
- [ ] Approval requests
- [ ] Completion notifications

### 4.3 Offline Support
- [ ] Queue actions when offline
- [ ] Sync when connected
- [ ] Conflict resolution

---

## Phase 5: Polish and Optimization 💎

### 5.1 UI/UX Improvements
- [ ] Animations and transitions
- [ ] Pull-to-refresh
- [ ] Empty states
- [ ] Error handling UI

### 5.2 Performance
- [ ] Image optimization
- [ ] List virtualization
- [ ] API response caching
- [ ] Bundle size optimization

### 5.3 Testing
- [ ] Unit tests for services
- [ ] Component testing
- [ ] Integration tests
- [ ] Manual test scenarios

---

## Phase 6: Release Preparation 🚀

### 6.1 App Store Assets
- [ ] App icon (1024x1024)
- [ ] Screenshots (various sizes)
- [ ] App description
- [ ] Keywords

### 6.2 TestFlight Beta
- [ ] Build for TestFlight
- [ ] Internal testing
- [ ] External beta testers
- [ ] Feedback incorporation

### 6.3 App Store Submission
- [ ] Final build
- [ ] App Store Connect setup
- [ ] Submit for review
- [ ] Handle review feedback

---

## Technical Decisions Log

### Architecture Decisions
1. **State Management**: React Context API (simpler than Redux for this app size)
2. **Navigation**: React Navigation v6 (industry standard)
3. **API Client**: Axios (robust interceptor support)
4. **Storage**: AsyncStorage (sufficient for our needs)
5. **Authentication**: JWT with secure storage

### Style Guide
- **Colors**: Defined in `styles/colors.js`
- **Typography**: Consistent text styles in `styles/typography.js`
- **Spacing**: 8-point grid system
- **Components**: Functional components with hooks

### API Integration Patterns
- All API calls through central client
- Consistent error handling
- Loading states for all async operations
- Optimistic updates where appropriate

---

## Known Issues & TODOs

### Current Issues
- None yet (project just started)

### Future Enhancements
- [ ] iPad support
- [ ] Apple Watch companion app
- [ ] Widgets for iOS 14+
- [ ] Siri shortcuts
- [ ] Family sharing integration

---

## Development Notes

### Useful Commands
```bash
# Run on iOS simulator
npm run ios

# Run on specific simulator
npm run ios -- --simulator="iPhone 14 Pro"

# Run on physical device
# Connect device, select in Xcode, then run

# Clear build cache
cd ios && rm -rf build && cd ..
cd ios && pod deintegrate && pod install && cd ..

# Reset Metro cache
npm start -- --reset-cache
```

### Debugging Tips
1. Shake device or Cmd+D for dev menu
2. Enable "Debug JS Remotely" for Chrome DevTools
3. Use Reactotron for advanced debugging
4. Check Metro terminal for build errors

### Performance Monitoring
- Use React DevTools Profiler
- Monitor bundle size with `npx react-native-bundle-visualizer`
- Test on older devices (iPhone 8 or newer)

---

## Phase 0 Completion Notes

### Key Accomplishments:
- Successfully set up React Native 0.80.0 with all dependencies
- Resolved Ruby/CocoaPods compatibility issues using rbenv
- Fixed Xcode build issues (sandbox permissions, script errors)
- App running on physical iPhone via both Xcode and CLI

### Metro Bundler Understanding:
- **Role**: JavaScript bundler that transforms and serves code to the app
- **Development**: App connects to Metro on Mac for hot reloading
- **Process**: Native app shell + JavaScript loaded dynamically from Metro

### Build Commands:
```bash
# Start Metro bundler (Terminal 1)
npm start

# Run on device (Terminal 2)
npx react-native run-ios --device
# or
npm run ios -- --device
```

---

## Next Session Starting Point

**Current Status**: Phase 0 COMPLETED ✅ - App running on physical device

**Ready for Phase 1**: Core Infrastructure and Authentication
1. Implement API client with Axios
2. Create storage service with AsyncStorage
3. Build authentication service with JWT support
4. Create login screen with biometric support
5. Set up navigation and auth context

**API Configuration**:
- Local: http://localhost:8000/api/v1
- Production: Will be configured later