# Home Deployment Guide for Chores Tracker App

## Understanding How Your App Works Without Dev Server

Currently, when connected via USB, your app runs in development mode:
- **Metro bundler** serves JavaScript files from your Mac
- **Hot reloading** allows instant updates
- **Development server** handles all JS bundling

For standalone operation, the app needs a **release build**:
- All JavaScript is bundled into the app package
- No external server connection needed
- API calls go directly to `http://chores.arigsela.com`
- App runs entirely on the device

## Deployment Strategy for Your Home Network

Given your setup:
- ✅ API running at `http://chores.arigsela.com` (home network only)
- ✅ Multiple iOS devices (iPhones, iPad Pro)
- ✅ Android devices
- ✅ Willingness to pay for Apple Developer account

### Recommended Approach

**iOS: TestFlight** (Requires Apple Developer Account - $99/year)
**Android: Direct APK Installation** (Free)

## iOS Deployment via TestFlight

### Step 1: Apple Developer Account Setup
1. Visit [developer.apple.com](https://developer.apple.com)
2. Enroll in the Apple Developer Program ($99/year)
3. Wait for approval (usually 24-48 hours)

### Step 2: Configure Your App for Release
```bash
# In your project directory
cd ios

# Open Xcode
open ChoresTrackerMobile.xcworkspace
```

In Xcode:
1. Select your project in the navigator
2. Under "Signing & Capabilities":
   - Team: Select your Apple Developer account
   - Bundle Identifier: `com.yourname.chorestracker` (make it unique)
   - Automatically manage signing: ✓

### Step 3: Build for Release
```bash
# Clean build folder
cd ios && rm -rf build && cd ..

# Build release version
npx react-native run-ios --configuration Release
```

### Step 4: Archive and Upload to TestFlight
In Xcode:
1. Select "Any iOS Device" as the build target
2. Product → Archive
3. Once archived, click "Distribute App"
4. Choose "App Store Connect" → "Upload"
5. Follow the wizard to upload

### Step 5: Configure TestFlight
1. Log into [App Store Connect](https://appstoreconnect.apple.com)
2. Select your app
3. Go to TestFlight tab
4. Add Internal Testers (family members):
   - Click (+) next to "Internal Testing"
   - Add family members' Apple IDs
   - They'll receive an email invitation

### Step 6: Family Installation
Family members:
1. Download TestFlight from App Store
2. Accept email invitation
3. Install your app through TestFlight
4. App auto-updates when you push new builds

## Android Deployment

### Step 1: Generate Signed APK
```bash
# Navigate to android directory
cd android

# Generate release APK
./gradlew assembleRelease
```

The APK will be at: `android/app/build/outputs/apk/release/app-release.apk`

### Step 2: Configure for Unsigned APK (Easier for Home Use)
Edit `android/app/build.gradle`:
```gradle
android {
    ...
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
            // Remove signing config for home use
        }
    }
}
```

Then rebuild:
```bash
./gradlew clean assembleRelease
```

### Step 3: Distribute to Family
Options:
1. **Email**: Send APK as attachment
2. **Cloud Storage**: Upload to Google Drive/Dropbox
3. **Local Web Server**: Host on your home server
4. **USB Transfer**: Direct device transfer

### Step 4: Installation on Android Devices
On each Android device:
1. Settings → Security → Enable "Unknown Sources"
2. Download/receive the APK
3. Tap to install
4. Grant permissions when prompted

## Critical Network Configuration

### Ensure API Accessibility
Your API at `http://chores.arigsela.com` must be:
1. **Accessible on home WiFi** - All devices on same network
2. **Static hostname** - Ensure DNS resolution works
3. **Firewall configured** - Port 8000 open internally

### Already Configured in Your App:
✅ iOS Info.plist allows HTTP for `chores.arigsela.com`
✅ Android will need similar configuration

Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

## Quick Build Commands Reference

### iOS Release Build
```bash
# TestFlight build (requires signing)
npx react-native run-ios --configuration Release

# Or build in Xcode:
# Product → Archive → Distribute App
```

### Android Release Build
```bash
cd android
./gradlew assembleRelease
# Find APK at: android/app/build/outputs/apk/release/
```

## Maintenance and Updates

### iOS (TestFlight)
1. Make code changes
2. Increment build number in Xcode
3. Archive and upload new build
4. Family members get automatic updates

### Android
1. Make code changes
2. Generate new APK
3. Redistribute to family
4. They manually install update

## Troubleshooting

### App Can't Connect to API
- Verify device is on home WiFi
- Check `http://chores.arigsela.com/docs` in device browser
- Ensure no VPN is active
- Verify API is running

### iOS Build Issues
- Ensure Apple Developer account is active
- Check provisioning profiles in Xcode
- Clean derived data: `rm -rf ~/Library/Developer/Xcode/DerivedData`

### Android Installation Blocked
- Enable "Install from Unknown Sources"
- Some devices: Settings → Apps → Special Access → Install Unknown Apps
- Select your file manager/browser and allow

## Cost Summary

**iOS**:
- Apple Developer Account: $99/year
- Covers unlimited family devices
- Professional distribution via TestFlight

**Android**:
- Free (direct APK distribution)
- Optional: Google Play Console $25 one-time

## Next Steps

1. **Immediate**: Test Android APK distribution (free, quick)
2. **This Week**: Enroll in Apple Developer Program
3. **Configure**: Unique bundle IDs and app signing
4. **Deploy**: TestFlight for iOS, APK for Android
5. **Optional**: Consider VPN for remote access

## Family Device Summary

| Device | Platform | Distribution Method | Cost |
|--------|----------|-------------------|------|
| Your iPhone | iOS | TestFlight | $99/year |
| Daughter's iPad Pro | iOS | TestFlight | Included |
| Android Devices | Android | Direct APK | Free |

With this setup, your family can use the Chores Tracker app on all devices while connected to your home network, with automatic updates for iOS via TestFlight and manual updates for Android.