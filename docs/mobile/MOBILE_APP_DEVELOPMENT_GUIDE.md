# Mobile App Development Guide

## Overview

The Chores Tracker mobile application is built with **React Native** using **Expo**, enabling deployment to both iOS and Android from a single codebase. The mobile app shares approximately 90% of its code with the React Native Web frontend, maximizing code reuse and development efficiency.

### Technology Stack

- **Framework**: React Native (v0.79.5) with Expo (v53)
- **Language**: TypeScript
- **Navigation**: React Navigation 7.x
- **State Management**: React Context API
- **API Client**: Axios with JWT authentication
- **Storage**: AsyncStorage for offline persistence
- **Testing**: Jest with React Native Testing Library
- **Build Tool**: Expo Application Services (EAS)

---

## Table of Contents

1. [Why React Native?](#why-react-native)
2. [Framework Comparison](#framework-comparison)
3. [Development Environment Setup](#development-environment-setup)
4. [Running the App](#running-the-app)
5. [Development Workflow](#development-workflow)
6. [Testing Strategies](#testing-strategies)
7. [Platform-Specific Considerations](#platform-specific-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)
10. [Building for Production](#building-for-production)

---

## Why React Native?

### Strategic Decision Factors

**Code Sharing (90%)**:
- Single codebase for iOS, Android, and Web
- Shared business logic, API integration, and components
- Reduced development and maintenance costs

**Developer Experience**:
- Fast Refresh for instant updates during development
- Strong TypeScript support
- Rich ecosystem of libraries and tools
- Familiar React patterns and hooks

**Performance**:
- Near-native performance for most use cases
- Direct bridge to native APIs when needed
- Efficient rendering with React's reconciliation

**Community & Support**:
- Large, active community
- Extensive documentation and resources
- Regular updates and improvements
- Strong corporate backing (Meta/Facebook)

**Time to Market**:
- Rapid prototyping and iteration
- Hot reloading for immediate feedback
- Easy deployment to app stores
- Built-in update mechanism (Expo Updates)

---

## Framework Comparison

### React Native vs Flutter vs Native

| Aspect | React Native | Flutter | Native (Swift/Kotlin) |
|--------|-------------|---------|----------------------|
| **Language** | JavaScript/TypeScript | Dart | Swift/Kotlin |
| **Performance** | Near-native (~95%) | Near-native (~98%) | 100% native |
| **Code Reuse** | iOS, Android, Web | iOS, Android, (Web beta) | None |
| **Development Speed** | Fast (Hot Reload) | Fast (Hot Reload) | Moderate |
| **Learning Curve** | Low (if know React) | Moderate | High |
| **UI Components** | Native + Custom | Custom widgets | Platform native |
| **Community** | Very Large | Growing | Platform-specific |
| **Tooling** | Excellent | Excellent | Platform tools |
| **Package Ecosystem** | Extensive | Growing | Platform stores |
| **Our Code Sharing** | 90% with web | Limited | 0% |

### Why Not Flutter?

While Flutter offers excellent performance and a unified widget system, we chose React Native for:

1. **Web Integration**: Our existing React Native Web frontend shares 90% code with mobile
2. **Team Expertise**: Existing JavaScript/TypeScript knowledge
3. **Ecosystem Alignment**: Seamless integration with web development tools
4. **Proven Solution**: Battle-tested in production by major companies

### Why Not Native?

Native development would offer maximum performance but:

1. **Development Cost**: 3x effort (iOS + Android + Web)
2. **Maintenance Burden**: Separate codebases to maintain
3. **Feature Parity**: Harder to keep platforms in sync
4. **Unnecessary for Use Case**: Chores Tracker doesn't require native-only features

---

## Development Environment Setup

### Prerequisites

#### macOS (for iOS and Android)

1. **Node.js and npm**:
   ```bash
   # Install Node.js 18+ (LTS recommended)
   brew install node

   # Verify installation
   node --version  # Should be 18.x or higher
   npm --version   # Should be 9.x or higher
   ```

2. **Watchman** (recommended for better performance):
   ```bash
   brew install watchman
   ```

3. **Git**:
   ```bash
   brew install git
   ```

4. **Xcode** (for iOS development):
   - Download from Mac App Store
   - Version 14.0 or later required
   - Install Command Line Tools:
     ```bash
     xcode-select --install
     ```
   - Accept license:
     ```bash
     sudo xcodebuild -license accept
     ```
   - Install iOS Simulator:
     - Open Xcode → Preferences → Components
     - Download iOS Simulator

5. **Android Studio** (for Android development):
   - Download from https://developer.android.com/studio
   - Install Android SDK:
     - During installation, select "Android SDK"
     - Minimum SDK version: API 21 (Android 5.0)
     - Recommended SDK: API 33 (Android 13)
   - Configure environment variables in `~/.zshrc` or `~/.bash_profile`:
     ```bash
     export ANDROID_HOME=$HOME/Library/Android/sdk
     export PATH=$PATH:$ANDROID_HOME/emulator
     export PATH=$PATH:$ANDROID_HOME/platform-tools
     ```
   - Reload shell:
     ```bash
     source ~/.zshrc  # or ~/.bash_profile
     ```

6. **Expo CLI**:
   ```bash
   npm install -g expo-cli
   ```

#### Windows (Android only)

1. **Node.js**: Download from https://nodejs.org/
2. **Git**: Download from https://git-scm.com/
3. **Android Studio**: Follow Android setup above
4. **Environment Variables**:
   ```
   ANDROID_HOME=C:\Users\YourUsername\AppData\Local\Android\Sdk
   PATH=%PATH%;%ANDROID_HOME%\platform-tools
   PATH=%PATH%;%ANDROID_HOME%\emulator
   ```

#### Linux (Android only)

1. **Node.js**:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Android Studio**: Follow installation for your distribution
3. Set environment variables similar to macOS

---

### Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/chores-tracker.git
   cd chores-tracker/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env with your settings
   # For local development:
   API_URL=http://localhost:8000/api/v1
   ```

4. **Verify installation**:
   ```bash
   npm run type-check  # Check TypeScript
   npm run lint        # Check code style
   ```

---

## Running the App

### Development Modes

#### 1. Expo Go (Quick Start)

**Best for**: Initial development, quick testing, component development

```bash
cd frontend

# Start Expo dev server
npm start
# or
expo start
```

**Using Expo Go App**:
1. Install "Expo Go" from App Store (iOS) or Play Store (Android)
2. Scan QR code from terminal
3. App loads in Expo Go

**Limitations**:
- Cannot use custom native modules
- Limited to Expo SDK features
- Not suitable for production

#### 2. iOS Simulator

**Requirements**: macOS with Xcode

```bash
cd frontend

# Start on iOS simulator
npm run ios

# Or with Expo CLI
expo start --ios

# Open specific simulator
expo start --ios --simulator="iPhone 14 Pro"
```

**Managing Simulators**:
```bash
# List available simulators
xcrun simctl list devices

# Open Simulator app
open -a Simulator

# Create new simulator
xcrun simctl create "iPhone 14 Pro" "iPhone 14 Pro"
```

**Simulator Shortcuts**:
- **⌘ + D**: Open developer menu
- **⌘ + R**: Reload app
- **⌘ + K**: Toggle keyboard
- **⌘ + Shift + H**: Home button

#### 3. iOS Physical Device

**Requirements**:
- Apple Developer account (free tier works)
- iOS device with cable
- Xcode configured with your Apple ID

```bash
# Connect device via USB
# Trust computer on device if prompted

# Run on connected device
npm run ios --device

# Or specify device
npm run ios --device="Your iPhone Name"
```

**Troubleshooting Device Connection**:
```bash
# List connected devices
xcrun xctrace list devices

# Check device logs
idevicesyslog  # Install via: brew install libimobiledevice
```

#### 4. Android Emulator

**Requirements**: Android Studio with AVD Manager

```bash
cd frontend

# List available emulators
emulator -list-avds

# Start emulator manually
emulator -avd Pixel_5_API_33

# Run on Android emulator
npm run android

# Or with Expo CLI
expo start --android
```

**Creating Android Virtual Device (AVD)**:
1. Open Android Studio → Tools → AVD Manager
2. Click "Create Virtual Device"
3. Select device (e.g., Pixel 5)
4. Select system image (API 33 recommended)
5. Configure performance (enable GPU acceleration)
6. Finish and launch

**Emulator Shortcuts**:
- **⌘ + M** (macOS) / **Ctrl + M** (Windows/Linux): Developer menu
- **R + R**: Reload app
- **Ctrl + Shift + P**: Power menu

#### 5. Android Physical Device

**Requirements**: Android device with USB debugging enabled

**Enable Developer Mode**:
1. Settings → About Phone
2. Tap "Build Number" 7 times
3. Go back → Developer Options
4. Enable "USB Debugging"

```bash
# Connect device via USB
# Accept USB debugging prompt on device

# Verify device connection
adb devices

# Run on connected device
npm run android
```

**ADB Troubleshooting**:
```bash
# Restart ADB server
adb kill-server
adb start-server

# Check device status
adb devices -l

# View device logs
adb logcat | grep ReactNative
```

#### 6. Web Browser

```bash
cd frontend

# Run in web browser
npm run web

# Automatically opens http://localhost:8081
```

**Web-Specific Notes**:
- Some React Native features may not work (e.g., certain native modules)
- Styles may render differently
- Useful for rapid UI development

---

## Development Workflow

### Hot Reload & Fast Refresh

React Native provides **Fast Refresh** for instant updates:

**How it works**:
1. Save file in editor
2. App updates automatically in seconds
3. Component state is preserved
4. Only changed components re-render

**Triggering Manual Reload**:
```bash
# In terminal
r       # Reload app
d       # Open developer menu
i       # Run on iOS
a       # Run on Android
w       # Run on web
```

**Disabling Fast Refresh** (if needed):
- Open developer menu in app
- Toggle "Fast Refresh"

### Developer Menu

**Open Developer Menu**:
- **iOS Simulator**: ⌘ + D
- **iOS Device**: Shake device
- **Android Emulator**: ⌘ + M (macOS) / Ctrl + M (Windows/Linux)
- **Android Device**: Shake device

**Menu Options**:
- **Reload**: Refresh app
- **Debug Remote JS**: Debug in Chrome DevTools
- **Show Inspector**: Inspect element layout
- **Show Perf Monitor**: View FPS and memory
- **Toggle Element Inspector**: Select elements
- **Disable Fast Refresh**: Turn off hot reloading

### Debugging

#### 1. Console Logging

```typescript
// Basic logging
console.log('Debug message:', variable);
console.error('Error:', error);
console.warn('Warning:', warning);

// Structured logging
console.log('API Response:', JSON.stringify(response, null, 2));

// Conditional logging
if (__DEV__) {
  console.log('Development only log');
}
```

**View Logs**:
```bash
# iOS Simulator
xcrun simctl spawn booted log stream --level debug --process Expo

# Android Emulator
adb logcat *:S ReactNative:V ReactNativeJS:V

# Expo dev server
# Logs appear in terminal automatically
```

#### 2. React Native Debugger

**Install**:
```bash
brew install --cask react-native-debugger
```

**Usage**:
1. Open React Native Debugger app
2. Set port to 19000 (Expo default)
3. Open Developer Menu in app
4. Select "Debug Remote JS"
5. Use Chrome DevTools interface

**Features**:
- Redux DevTools integration
- React DevTools
- Network inspection
- Console logs
- Breakpoint debugging

#### 3. Flipper (Advanced)

**Install**:
```bash
brew install --cask flipper
```

**Features**:
- Network inspection
- Layout inspector
- Database viewer
- Performance profiling
- Plugin system

**Setup**:
- Expo apps require custom development client
- See: https://docs.expo.dev/development/tools/

#### 4. Chrome DevTools

**Setup**:
1. Open Developer Menu
2. Select "Debug Remote JS"
3. Chrome opens automatically
4. Open DevTools (⌘ + Option + I)

**Tips**:
- Set breakpoints in source code
- Use debugger; statement
- Inspect network requests
- View component hierarchy

### Code Quality Tools

#### ESLint (Code Linting)

```bash
# Run linter
npm run lint

# Auto-fix issues
npm run lint:fix
```

**Configuration**: `.eslintrc.json`

#### Prettier (Code Formatting)

```bash
# Format code
npm run format

# Check formatting
npm run format:check
```

**Configuration**: `.prettierrc`

#### TypeScript (Type Checking)

```bash
# Run type checker
npm run type-check
```

**Configuration**: `tsconfig.json`

---

## Testing Strategies

### Test Structure

```
frontend/src/
├── __tests__/           # Top-level integration tests
├── components/
│   ├── __tests__/       # Component unit tests
│   ├── ChoreCard.tsx
│   └── ChoreCard.test.tsx
├── screens/
│   ├── __tests__/       # Screen integration tests
│   └── LoginScreen.tsx
└── api/
    ├── __tests__/       # API client tests
    └── client.ts
```

### Unit Testing

**Example Component Test**:

```typescript
// src/components/__tests__/ChoreCard.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ChoreCard } from '../ChoreCard';

describe('ChoreCard', () => {
  const mockChore = {
    id: 1,
    title: 'Mow the lawn',
    description: 'Front and back yard',
    reward: 15.0,
    is_completed: false,
  };

  it('renders chore details correctly', () => {
    const { getByText } = render(<ChoreCard chore={mockChore} />);

    expect(getByText('Mow the lawn')).toBeTruthy();
    expect(getByText('Front and back yard')).toBeTruthy();
    expect(getByText('$15.00')).toBeTruthy();
  });

  it('calls onComplete when complete button pressed', () => {
    const onComplete = jest.fn();
    const { getByText } = render(
      <ChoreCard chore={mockChore} onComplete={onComplete} />
    );

    fireEvent.press(getByText('Complete'));
    expect(onComplete).toHaveBeenCalledWith(1);
  });
});
```

### Integration Testing

**Example Screen Test**:

```typescript
// src/screens/__tests__/LoginScreen.test.tsx
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { LoginScreen } from '../LoginScreen';
import { AuthProvider } from '@/contexts/AuthContext';

describe('LoginScreen', () => {
  it('validates empty credentials', async () => {
    const { getByText, getByPlaceholderText } = render(
      <AuthProvider>
        <LoginScreen onNavigateToRegister={() => {}} />
      </AuthProvider>
    );

    fireEvent.press(getByText('Sign In'));

    await waitFor(() => {
      expect(getByText(/enter both username and password/i)).toBeTruthy();
    });
  });

  it('submits valid credentials', async () => {
    const { getByText, getByPlaceholderText } = render(
      <AuthProvider>
        <LoginScreen onNavigateToRegister={() => {}} />
      </AuthProvider>
    );

    fireEvent.changeText(
      getByPlaceholderText('Enter your username'),
      'test_user'
    );
    fireEvent.changeText(
      getByPlaceholderText('Enter your password'),
      'password123'
    );
    fireEvent.press(getByText('Sign In'));

    await waitFor(() => {
      // Expect navigation to home or loading state
    });
  });
});
```

### Running Tests

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- ChoreCard.test.tsx

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Debug tests
npm run test:debug
```

### Test Coverage

```bash
# Generate coverage report
npm run test:coverage

# View HTML report
open coverage/lcov-report/index.html
```

**Coverage Targets**:
- Unit tests: >80% coverage
- Integration tests: Cover critical user flows
- Components: Test all props and user interactions
- API client: Mock all endpoints

### E2E Testing (Advanced)

For end-to-end testing, consider:

**Detox** (React Native E2E):
```bash
npm install --save-dev detox
```

**Maestro** (Cross-platform):
- https://maestro.mobile.dev/
- YAML-based test flows

---

## Platform-Specific Considerations

### iOS Development

#### App Configuration

**`app.json`** (iOS section):
```json
{
  "expo": {
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.yourcompany.chorestracker",
      "buildNumber": "1.0.0",
      "infoPlist": {
        "NSCameraUsageDescription": "Take photos of completed chores",
        "NSPhotoLibraryUsageDescription": "Upload chore completion photos"
      }
    }
  }
}
```

#### Common iOS Issues

**Safe Area Insets**:
```typescript
import { SafeAreaView } from 'react-native-safe-area-context';

// Use SafeAreaView for proper spacing on notched devices
<SafeAreaView style={styles.container}>
  {/* Your content */}
</SafeAreaView>
```

**Keyboard Avoiding**:
```typescript
import { KeyboardAvoidingView, Platform } from 'react-native';

<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
  style={styles.container}
>
  {/* Forms */}
</KeyboardAvoidingView>
```

**Status Bar**:
```typescript
import { StatusBar } from 'expo-status-bar';

// Auto-adjusts for light/dark mode
<StatusBar style="auto" />
```

#### iOS Simulator Tips

```bash
# Reset simulator
xcrun simctl erase all

# Take screenshot
xcrun simctl io booted screenshot screenshot.png

# Record video
xcrun simctl io booted recordVideo video.mp4

# Open simulator folder
open ~/Library/Developer/CoreSimulator/Devices/
```

### Android Development

#### App Configuration

**`app.json`** (Android section):
```json
{
  "expo": {
    "android": {
      "package": "com.yourcompany.chorestracker",
      "versionCode": 1,
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ]
    }
  }
}
```

#### Common Android Issues

**Back Button Handling**:
```typescript
import { BackHandler } from 'react-native';
import { useEffect } from 'react';

useEffect(() => {
  const backHandler = BackHandler.addEventListener(
    'hardwareBackPress',
    () => {
      // Custom back button logic
      return true; // Prevent default behavior
    }
  );

  return () => backHandler.remove();
}, []);
```

**Edge-to-Edge Display**:
```json
{
  "expo": {
    "android": {
      "edgeToEdgeEnabled": true
    }
  }
}
```

#### Android Emulator Performance

**Speed up emulator**:
1. AVD Manager → Edit AVD
2. Graphics: Hardware (GLES 2.0)
3. RAM: 2048 MB minimum
4. Internal Storage: 2 GB minimum
5. Enable Multi-Core CPU

**Command line options**:
```bash
# Run with GPU acceleration
emulator -avd Pixel_5_API_33 -gpu host

# Increase RAM
emulator -avd Pixel_5_API_33 -memory 4096
```

### Platform Detection

```typescript
import { Platform } from 'react-native';

// Conditional code
if (Platform.OS === 'ios') {
  // iOS-specific code
} else if (Platform.OS === 'android') {
  // Android-specific code
} else if (Platform.OS === 'web') {
  // Web-specific code
}

// Platform-specific values
const styles = StyleSheet.create({
  container: {
    paddingTop: Platform.select({
      ios: 20,
      android: 25,
      web: 0,
    }),
  },
});

// Platform-specific components
const Component = Platform.select({
  ios: () => require('./ComponentIOS'),
  android: () => require('./ComponentAndroid'),
  default: () => require('./ComponentDefault'),
})();
```

### Platform-Specific Files

React Native supports platform-specific file extensions:

```
components/
├── Button.ios.tsx       # iOS version
├── Button.android.tsx   # Android version
└── Button.tsx           # Default/Web version
```

---

## Performance Optimization

### Rendering Performance

#### 1. Optimize Re-renders

```typescript
import React, { memo, useCallback, useMemo } from 'react';

// Memoize components
const ChoreCard = memo(({ chore, onComplete }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.chore.id === nextProps.chore.id;
});

// Memoize callbacks
const handleComplete = useCallback((choreId) => {
  completeChore(choreId);
}, []);

// Memoize expensive calculations
const sortedChores = useMemo(() => {
  return chores.sort((a, b) => a.title.localeCompare(b.title));
}, [chores]);
```

#### 2. FlatList Optimization

```typescript
import { FlatList } from 'react-native';

<FlatList
  data={chores}
  renderItem={({ item }) => <ChoreCard chore={item} />}
  keyExtractor={(item) => item.id.toString()}

  // Performance props
  removeClippedSubviews={true}           // Unmount off-screen views
  maxToRenderPerBatch={10}               // Items per render batch
  updateCellsBatchingPeriod={50}         // Batch update frequency
  initialNumToRender={10}                // Initial items
  windowSize={5}                         // Viewport multiplier

  // Optimize item updates
  getItemLayout={(data, index) => ({     // Skip measurement
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
/>
```

#### 3. Image Optimization

```typescript
import { Image } from 'react-native';
import FastImage from 'react-native-fast-image';

// Use FastImage for better performance
<FastImage
  source={{ uri: imageUrl, priority: FastImage.priority.normal }}
  style={styles.image}
  resizeMode={FastImage.resizeMode.contain}
/>

// Lazy load images
<Image
  source={{ uri: imageUrl }}
  style={styles.image}
  loadingIndicatorSource={require('./placeholder.png')}
/>
```

### Bundle Size Optimization

```bash
# Analyze bundle size
npx react-native-bundle-visualizer

# Tree-shake unused code
# Import only what you need
import { View } from 'react-native';  // Good
import * as RN from 'react-native';   // Bad (imports everything)
```

### Network Performance

```typescript
// API client optimization
import axios from 'axios';

const apiClient = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request batching
const batchRequests = async (requests) => {
  return Promise.all(requests.map(req => apiClient(req)));
};

// Response caching
const cache = new Map();
const cachedGet = async (url) => {
  if (cache.has(url)) {
    return cache.get(url);
  }
  const response = await apiClient.get(url);
  cache.set(url, response.data);
  return response.data;
};
```

### Performance Monitoring

```typescript
// Use Expo's Performance API
import { PerformanceObserver } from 'expo-performance';

const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  entries.forEach((entry) => {
    console.log(`${entry.name}: ${entry.duration}ms`);
  });
});

observer.observe({ entryTypes: ['measure'] });

// Measure custom operations
performance.mark('api-call-start');
await fetchChores();
performance.mark('api-call-end');
performance.measure('api-call', 'api-call-start', 'api-call-end');
```

---

## Troubleshooting

### Common Issues and Solutions

#### Metro Bundler Issues

**Problem**: Cache-related errors, stale builds

**Solution**:
```bash
# Clear all caches
npm start -- --clear

# Or manually
rm -rf node_modules
rm -rf .expo
rm package-lock.json
npm install
npm start -- --reset-cache
```

#### Build Failures

**iOS Build Fails**:
```bash
# Clean Xcode build folder
cd ios
xcodebuild clean

# Clear derived data
rm -rf ~/Library/Developer/Xcode/DerivedData

# Reinstall pods
cd ios
pod deintegrate
pod install
```

**Android Build Fails**:
```bash
# Clean Gradle build
cd android
./gradlew clean
./gradlew cleanBuildCache

# Reset Gradle
rm -rf ~/.gradle/caches/
```

#### Cannot Connect to Backend

**Problem**: Mobile app can't reach localhost:8000

**iOS Simulator Solution**:
```typescript
// Use localhost directly
const API_URL = 'http://localhost:8000/api/v1';
```

**Android Emulator Solution**:
```typescript
// Android emulator uses 10.0.2.2 for host machine
const API_URL = Platform.select({
  android: 'http://10.0.2.2:8000/api/v1',
  ios: 'http://localhost:8000/api/v1',
});
```

**Physical Device Solution**:
```typescript
// Use your computer's IP address
const API_URL = 'http://192.168.1.100:8000/api/v1';

// Or configure .env
// .env
API_URL=http://192.168.1.100:8000/api/v1
```

**Find your IP**:
```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I

# Windows
ipconfig
```

#### Port Already in Use

```bash
# Kill process on port 8081 (Metro bundler)
lsof -ti:8081 | xargs kill -9

# Or use different port
npm start -- --port 8082
```

#### AsyncStorage Errors

```bash
# Clear AsyncStorage in app
import AsyncStorage from '@react-native-async-storage/async-storage';
await AsyncStorage.clear();

# Or reset simulator/emulator entirely
```

#### TypeScript Errors

```bash
# Regenerate TypeScript cache
npm run type-check

# Update @types
npm install --save-dev @types/react@latest @types/react-native@latest
```

---

## Building for Production

### Expo Application Services (EAS)

#### Setup

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo account
eas login

# Configure project
eas build:configure
```

#### Build iOS

```bash
# Development build (for testing)
eas build --platform ios --profile development

# Production build (for App Store)
eas build --platform ios --profile production

# Submit to App Store
eas submit --platform ios
```

#### Build Android

```bash
# Development build (APK)
eas build --platform android --profile development

# Production build (AAB for Play Store)
eas build --platform android --profile production

# Submit to Play Store
eas submit --platform android
```

#### Build Configuration

**`eas.json`**:
```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "production": {
      "distribution": "store",
      "env": {
        "API_URL": "https://api.chorestracker.com/api/v1"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your.email@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCDE12345"
      },
      "android": {
        "serviceAccountKeyPath": "./service-account.json",
        "track": "production"
      }
    }
  }
}
```

### Over-the-Air (OTA) Updates

```bash
# Publish update (doesn't require app store review)
eas update --branch production --message "Bug fixes"

# Rollback to previous version
eas update:rollback --branch production
```

### Pre-Release Checklist

- [ ] Update version in `app.json`
- [ ] Run full test suite (`npm test`)
- [ ] Test on real iOS device
- [ ] Test on real Android device
- [ ] Verify API endpoints (production URLs)
- [ ] Check analytics integration
- [ ] Test offline functionality
- [ ] Verify push notifications
- [ ] Review app store screenshots
- [ ] Update app store description
- [ ] Test in-app purchases (if applicable)
- [ ] Security audit (dependencies, secrets)

---

## Additional Resources

### Documentation
- **React Native**: https://reactnative.dev/
- **Expo**: https://docs.expo.dev/
- **React Navigation**: https://reactnavigation.org/
- **TypeScript**: https://www.typescriptlang.org/docs/

### Tools
- **React Native Debugger**: https://github.com/jhen0409/react-native-debugger
- **Flipper**: https://fbflipper.com/
- **Reactotron**: https://github.com/infinitered/reactotron

### Learning Resources
- **React Native Express**: https://www.reactnative.express/
- **Expo Snack**: https://snack.expo.dev/ (Online playground)
- **React Native Community**: https://www.reactnative.community/

### Internal Documentation
- [React Native Implementation Guide](./REACT_NATIVE_IMPLEMENTATION.md)
- [JWT Authentication Guide](../api/JWT_AUTH_EXPLAINER.md)
- [API Documentation](http://localhost:8000/docs)

---

**Last Updated**: 2025-11-23
**React Native Version**: 0.79.5
**Expo SDK**: 53
