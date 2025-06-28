# VS Code Testing Instructions

## Quick Start

### Option 1: Using VS Code Terminal (Easiest)

1. **Open VS Code integrated terminal** (Cmd+`)
2. **Split terminal** into 3 panes (click split icon)

**Terminal 1 - Backend:**
```bash
cd ..
docker compose up
```

**Terminal 2 - Metro:**
```bash
npm start
```

**Terminal 3 - Run App:**
```bash
# For Simulator (no phone needed):
npm run ios:simulator

# For Physical Device:
npm run ios:device
```

### Option 2: Using VS Code Tasks (Cmd+Shift+P)

1. Press `Cmd+Shift+P`
2. Type "Tasks: Run Task"
3. Select one of:
   - **"Full Dev Environment (Simulator)"** - Starts everything
   - **"Run iOS Simulator"** - Just the app
   - **"Run iOS Device"** - For physical device

### Option 3: Using NPM Scripts Panel

1. Look for NPM Scripts in VS Code sidebar
2. Click play button next to:
   - `ios:simulator` - Run on simulator
   - `ios:device` - Run on physical device
   - `dev:simulator` - Run with localhost API

## Switching Between Simulator and Device

### For Simulator Testing:
```bash
# In .env file:
API_URL=http://localhost:8000/api/v1

# Then run:
npm run ios:simulator
```

### For Device Testing:
```bash
# In .env file:
API_URL=http://192.168.0.250:8000/api/v1

# Then run:
npm run ios:device
```

## Hot Reload

After app is running:
- **Save any JS file** → App auto-reloads
- **No need to rebuild** for JS changes
- **Rebuild only needed** for native changes

## Keyboard Shortcuts

- `Cmd+R` in simulator: Reload app
- `Cmd+D` in simulator: Debug menu
- `Cmd+Shift+P`: VS Code command palette
- `Cmd+``: Toggle terminal

## Common Commands

```bash
# Clean and rebuild
cd ios && rm -rf build && cd ..
npx react-native run-ios --simulator="iPhone 16 Pro"

# Reset Metro cache
npm start -- --reset-cache

# List simulators
xcrun simctl list devices

# Open Xcode (if needed)
open ios/ChoresTrackerMobile.xcworkspace
```