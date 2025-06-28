# Mobile App Development Guide for Chores Tracker

This guide explains how to convert your web-based Chores Tracker application into a native iOS mobile app, covering different approaches and providing a detailed implementation roadmap.

## Table of Contents
1. [Overview of Mobile Development Approaches](#overview)
2. [Recommended Approach](#recommended-approach)
3. [Architecture Overview](#architecture-overview)
4. [React Native Implementation](#react-native-implementation)
5. [Flutter Implementation](#flutter-implementation)
6. [Authentication Flow](#authentication-flow)
7. [Development Environment Setup](#development-environment)
8. [Testing Strategy](#testing-strategy)
9. [Deployment to App Store](#deployment)
10. [Decision Framework](#decision-framework)

## Overview of Mobile Development Approaches {#overview}

### 1. Native Development (Swift/SwiftUI)
**Pros:**
- Best performance and native feel
- Full access to iOS features
- Apple's official framework

**Cons:**
- iOS only (no Android without separate codebase)
- Steeper learning curve
- No code reuse from web app

**When to choose:** When iOS-only is acceptable and performance is critical

### 2. Cross-Platform Frameworks

#### React Native
**Pros:**
- JavaScript-based (familiar for web developers)
- Large community and ecosystem
- Good performance (near-native)
- Single codebase for iOS and Android
- Can reuse some business logic concepts

**Cons:**
- Some platform-specific code still needed
- Bridge between JS and native can be a bottleneck
- Debugging can be complex

#### Flutter
**Pros:**
- Excellent performance (compiles to native code)
- Beautiful UI with Material Design
- Hot reload for fast development
- Strong typing with Dart
- Growing ecosystem

**Cons:**
- Dart language learning curve
- Larger app size
- Less mature than React Native

### 3. Progressive Web App (PWA)
**Pros:**
- Use existing web app code
- No app store approval needed
- Instant updates

**Cons:**
- Limited native features access
- No app store presence
- iOS support is limited

### 4. Hybrid (Ionic/Capacitor)
**Pros:**
- Wrap existing web app
- Quick to implement
- Access to some native features

**Cons:**
- Performance limitations
- Doesn't feel fully native
- Debugging complexity

## Recommended Approach {#recommended-approach}

For your Chores Tracker app, I recommend either **React Native** or **Flutter** based on these factors:

1. **Your existing backend is perfect** - FastAPI already provides JSON REST APIs
2. **Cross-platform potential** - Write once for iOS and Android
3. **Good performance** - Both offer near-native performance
4. **Active communities** - Extensive resources and packages available
5. **Professional appearance** - Can create truly native-feeling apps

### React Native vs Flutter Comparison

| Aspect | React Native | Flutter |
|--------|--------------|---------|
| Language | JavaScript/TypeScript | Dart |
| Performance | Good (JS bridge) | Excellent (compiled) |
| UI Components | Native platform widgets | Custom widgets |
| Learning Curve | Easier if you know JS | Moderate |
| Hot Reload | Yes | Yes |
| Community | Larger, more mature | Growing rapidly |
| Package Ecosystem | Extensive (npm) | Good and growing |
| Corporate Backing | Meta (Facebook) | Google |

## Architecture Overview {#architecture-overview}

Your mobile app architecture will leverage your existing backend:

```
┌─────────────────────┐     ┌─────────────────────┐
│   Mobile App (iOS)  │     │   Existing Backend  │
├─────────────────────┤     ├─────────────────────┤
│  React Native or    │     │     FastAPI         │
│     Flutter         │     │   (No changes!)     │
│                     │────►│                     │
│  - UI Components    │ HTTP│  - REST APIs        │
│  - State Management │     │  - JWT Auth         │
│  - API Client       │     │  - Business Logic   │
│  - Local Storage    │     │  - MySQL Database   │
└─────────────────────┘     └─────────────────────┘
```

**Key Points:**
- Your FastAPI backend remains unchanged
- Mobile app consumes the same REST endpoints
- JWT tokens stored securely on device
- All business logic stays in the backend

## React Native Implementation {#react-native-implementation}

### Step 1: Environment Setup

```bash
# Install Node.js and npm (if not already installed)
brew install node

# Install React Native CLI
npm install -g react-native-cli

# Install iOS development tools
# Xcode from Mac App Store (required)

# Install CocoaPods (iOS dependency manager)
sudo gem install cocoapods
```

### Step 2: Create React Native Project

```bash
# Create new React Native project
npx react-native init ChoresTracker

# Navigate to project
cd ChoresTracker

# Install additional dependencies
npm install axios react-navigation @react-native-async-storage/async-storage
npm install react-native-vector-icons react-native-elements
```

### Step 3: Project Structure

```
ChoresTracker/
├── src/
│   ├── api/
│   │   ├── client.js        # Axios configuration
│   │   └── endpoints.js     # API endpoint definitions
│   ├── components/
│   │   ├── ChoreCard.js
│   │   └── common/
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── HomeScreen.js
│   │   └── ChoreDetailsScreen.js
│   ├── navigation/
│   │   └── AppNavigator.js
│   ├── services/
│   │   └── authService.js
│   └── utils/
│       └── storage.js
├── App.js
└── package.json
```

### Step 4: API Client Configuration

```javascript
// src/api/client.js
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api/v1'  // Development
  : 'https://api.chorestracker.com/api/v1';  // Production

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

### Step 5: Authentication Service

```javascript
// src/services/authService.js
import apiClient from '../api/client';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const authService = {
  async login(username, password) {
    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      });
      
      const { access_token, user } = response.data;
      
      // Store token securely
      await AsyncStorage.setItem('authToken', access_token);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, user };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  },
  
  async logout() {
    await AsyncStorage.removeItem('authToken');
    await AsyncStorage.removeItem('user');
  },
  
  async getCurrentUser() {
    const userStr = await AsyncStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
};
```

### Step 6: Example Screen Component

```javascript
// src/screens/HomeScreen.js
import React, { useState, useEffect } from 'react';
import { 
  View, 
  FlatList, 
  Text, 
  StyleSheet,
  RefreshControl 
} from 'react-native';
import apiClient from '../api/client';
import ChoreCard from '../components/ChoreCard';

const HomeScreen = () => {
  const [chores, setChores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchChores = async () => {
    try {
      const response = await apiClient.get('/chores');
      setChores(response.data);
    } catch (error) {
      console.error('Error fetching chores:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchChores();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchChores();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={chores}
      renderItem={({ item }) => <ChoreCard chore={item} />}
      keyExtractor={(item) => item.id.toString()}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    />
  );
};

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default HomeScreen;
```

## Flutter Implementation {#flutter-implementation}

### Step 1: Environment Setup

```bash
# Install Flutter
# Download from https://flutter.dev/docs/get-started/install/macos

# Add Flutter to PATH
export PATH="$PATH:`pwd`/flutter/bin"

# Verify installation
flutter doctor

# Install Xcode and accept licenses
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
```

### Step 2: Create Flutter Project

```bash
# Create new Flutter project
flutter create chores_tracker

# Navigate to project
cd chores_tracker

# Add dependencies to pubspec.yaml
```

### Step 3: Dependencies (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.0
  provider: ^6.0.0
  jwt_decoder: ^2.0.1
  
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0
```

### Step 4: API Service

```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';
  
  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('authToken');
    
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
  
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('authToken', data['access_token']);
      return data;
    } else {
      throw Exception('Failed to login');
    }
  }
  
  Future<List<dynamic>> getChores() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/chores'),
      headers: headers,
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load chores');
    }
  }
}
```

### Step 5: Example Screen

```dart
// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _chores = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadChores();
  }

  Future<void> _loadChores() async {
    try {
      final chores = await _apiService.getChores();
      setState(() {
        _chores = chores;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading chores')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('My Chores'),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadChores,
              child: ListView.builder(
                itemCount: _chores.length,
                itemBuilder: (context, index) {
                  final chore = _chores[index];
                  return ListTile(
                    title: Text(chore['title']),
                    subtitle: Text(chore['description'] ?? ''),
                    trailing: Text('\$${chore['reward_amount']}'),
                  );
                },
              ),
            ),
    );
  }
}
```

## Authentication Flow {#authentication-flow}

The mobile authentication flow mirrors your web app:

```
1. User enters credentials
   ↓
2. POST /api/v1/auth/login
   ↓
3. Receive JWT token
   ↓
4. Store token securely
   - iOS Keychain (React Native)
   - Shared Preferences (Flutter)
   ↓
5. Include token in API requests
   Authorization: Bearer <token>
   ↓
6. Handle token expiration
   - Refresh token if implemented
   - Redirect to login if expired
```

### Security Considerations

1. **Secure Storage**
   - Never store tokens in plain text
   - Use platform-specific secure storage
   - Clear tokens on logout

2. **API Communication**
   - Always use HTTPS in production
   - Implement certificate pinning for extra security
   - Handle network errors gracefully

3. **Biometric Authentication**
   - Consider adding Face ID/Touch ID
   - Provides extra security layer
   - Better user experience

## Development Environment Setup {#development-environment}

### For React Native

```bash
# iOS Simulator
npx react-native run-ios

# Physical Device
# 1. Open Xcode
# 2. Select your device
# 3. Run the app

# Enable hot reload
# Shake device or Cmd+D in simulator
```

### For Flutter

```bash
# List available devices
flutter devices

# Run on iOS simulator
flutter run

# Run on specific device
flutter run -d "iPhone 14"

# Enable hot reload
# Press 'r' in terminal
```

### Connecting to Local Backend

For iOS Simulator:
- `localhost` or `127.0.0.1` works directly

For Physical Device:
1. Ensure device and computer are on same network
2. Use computer's local IP address
3. Update API base URL accordingly

```javascript
// React Native
const API_BASE_URL = Platform.select({
  ios: __DEV__ ? 'http://192.168.1.100:8000/api/v1' : PROD_URL,
  android: __DEV__ ? 'http://10.0.2.2:8000/api/v1' : PROD_URL,
});
```

## Testing Strategy {#testing-strategy}

### 1. Development Testing
- Use iOS Simulator for rapid iteration
- Test on physical device before release
- Test both parent and child user flows

### 2. API Integration Testing
- Use your existing Docker backend
- Test offline scenarios
- Verify token expiration handling

### 3. TestFlight Beta Testing
- Distribute to family members
- Gather feedback before App Store submission
- Test on various iOS versions

### Testing Checklist
- [ ] Login/logout flow
- [ ] Chore creation (parent)
- [ ] Chore completion (child)
- [ ] Approval process (parent)
- [ ] Offline behavior
- [ ] Push notifications (if implemented)
- [ ] Different screen sizes

## Deployment to App Store {#deployment}

### Prerequisites

1. **Apple Developer Account**
   - Cost: $99/year
   - Required for App Store distribution
   - Enables TestFlight beta testing

2. **App Store Connect Setup**
   - Create app record
   - Configure app information
   - Set up pricing (free)

### Build and Submit Process

#### React Native
```bash
# 1. Open Xcode
open ios/ChoresTracker.xcworkspace

# 2. Configure signing
# - Select your team
# - Set bundle identifier (com.yourname.chorestracker)

# 3. Archive build
# Product → Archive

# 4. Upload to App Store Connect
# Window → Organizer → Upload
```

#### Flutter
```bash
# 1. Update version in pubspec.yaml
version: 1.0.0+1

# 2. Build iOS app
flutter build ios --release

# 3. Open in Xcode
open ios/Runner.xcworkspace

# 4. Archive and upload
# Same as React Native steps
```

### App Store Requirements

1. **App Information**
   - App name and description
   - Keywords for search
   - Age rating (likely 4+)

2. **Screenshots**
   - Required sizes: 6.7", 6.5", 5.5"
   - Show key features
   - Include both parent and child views

3. **Privacy Policy**
   - Required for apps that collect user data
   - Host on your website
   - Explain data usage

4. **Review Process**
   - Usually 24-48 hours
   - Test thoroughly before submission
   - Provide demo account for reviewers

## Decision Framework {#decision-framework}

### Choose React Native if:
- ✅ You're comfortable with JavaScript
- ✅ You want to potentially share code/concepts with web
- ✅ You need access to many third-party packages
- ✅ You prefer web-like development experience

### Choose Flutter if:
- ✅ You want best performance
- ✅ You like strongly-typed languages
- ✅ You want pixel-perfect UI control
- ✅ You're willing to learn Dart

### Quick Start Recommendation

**For fastest results with your background:**
1. Start with React Native
2. Use Expo for even faster setup (with some limitations)
3. Implement core features first
4. Iterate based on user feedback

### Next Steps

1. **Week 1-2**: Environment setup and basic app structure
2. **Week 3-4**: Implement authentication and core screens
3. **Week 5-6**: Polish UI and handle edge cases
4. **Week 7**: TestFlight beta testing
5. **Week 8**: App Store submission

### Useful Resources

**React Native:**
- Official docs: https://reactnative.dev
- Navigation: https://reactnavigation.org
- UI components: https://reactnativeelements.com

**Flutter:**
- Official docs: https://flutter.dev
- Widget catalog: https://flutter.dev/docs/development/ui/widgets
- Pub.dev packages: https://pub.dev

**General:**
- Apple Human Interface Guidelines
- App Store Review Guidelines
- JWT.io for token debugging

Remember: Your existing FastAPI backend is already mobile-ready. Focus on creating a great mobile UI that consumes your existing APIs!