import { Platform, NativeModules } from 'react-native';
import DeviceInfo from 'react-native-device-info';
import Config from 'react-native-config';

// API URLs for different environments
const API_URLS = {
  simulator: 'http://localhost:8000/api/v1',
  device: 'http://192.168.0.250:8000/api/v1',
  production: 'http://chores.arigsela.com/api/v1',
};

// More reliable simulator detection
const isRunningOnSimulator = () => {
  if (Platform.OS === 'ios') {
    // Check multiple indicators for iOS simulator
    const isSimulator = 
      DeviceInfo.isEmulatorSync() || 
      (NativeModules.PlatformConstants && 
       NativeModules.PlatformConstants.interfaceIdiom === 'phone' && 
       !NativeModules.PlatformConstants.isDevice) ||
      DeviceInfo.getDeviceId() === 'Simulator';
    
    return isSimulator;
  }
  // For Android
  return DeviceInfo.isEmulatorSync();
};

export const getAPIUrl = () => {
  // Check if explicitly set in .env
  if (Config.API_URL && Config.API_URL !== 'auto') {
    // Handle special keywords
    if (Config.API_URL === 'production') {
      return API_URLS.production;
    }
    if (Config.API_URL === 'device') {
      return API_URLS.device;
    }
    if (Config.API_URL === 'simulator') {
      return API_URLS.simulator;
    }
    // Otherwise use the explicit URL
    return Config.API_URL;
  }
  
  // Auto-detect based on device type
  const isSimulator = isRunningOnSimulator();
  
  console.log('=== API URL Debug ===');
  console.log('Config.API_URL:', Config.API_URL);
  console.log('isSimulator:', isSimulator);
  console.log('Platform.OS:', Platform.OS);
  console.log('DeviceInfo.getDeviceId():', DeviceInfo.getDeviceId());
  console.log('DeviceInfo.isEmulatorSync():', DeviceInfo.isEmulatorSync());
  console.log('===================');
  
  if (isSimulator) {
    console.log('🖥️  Running on simulator, using localhost');
    return API_URLS.simulator;
  } else {
    console.log('📱 Running on physical device, using IP address');
    return API_URLS.device;
  }
};

// Export individual URLs for reference
export { API_URLS };