# React Native Testing Guide

## Testing Without Physical Device

### 1. iOS Simulator Setup

```bash
# List available simulators
xcrun simctl list devices

# Start specific simulator
open -a Simulator --args -DeviceTypeID "iPhone 16 Pro"

# Run app on simulator
npm run ios
```

### 2. Quick Testing Commands

```bash
# Test login functionality (simulator)
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=asela&password=password123&grant_type=password"

# Test with physical device (update IP)
# In .env file, change:
# API_URL=http://YOUR_MAC_IP:8000/api/v1
```

### 3. Metro Bundler Commands

```bash
# Start Metro
npm start

# Clear Metro cache
npm start -- --reset-cache

# Reload app in simulator
# Press Cmd+R in simulator
```

### 4. Common Issues

**Simulator not connecting to localhost:**
- Ensure backend is running: `docker compose up`
- Check backend logs: `docker compose logs -f api`

**Build taking too long:**
- Use Xcode directly for first build
- Subsequent builds will be faster

**Network errors:**
- Simulator uses localhost
- Physical device needs Mac's IP address

### 5. Testing Workflow

1. **Start Backend**
   ```bash
   cd /Users/arisela/git/chores-tracker
   docker compose up
   ```

2. **Start Metro (Terminal 1)**
   ```bash
   cd mobile
   npm start
   ```

3. **Run on Simulator (Terminal 2)**
   ```bash
   cd mobile
   npm run ios
   ```

4. **Hot Reload**
   - Make changes to JS files
   - Save file
   - App auto-reloads

### 6. Environment Switching

**For Simulator Testing:**
```bash
# .env file
API_URL=http://localhost:8000/api/v1
```

**For Device Testing:**
```bash
# .env file
API_URL=http://192.168.0.250:8000/api/v1
```

### 7. Debug Menu

- **iOS Simulator:** Cmd+D
- **Physical Device:** Shake device

Options:
- Reload
- Debug with Chrome
- Show Inspector
- Show Perf Monitor