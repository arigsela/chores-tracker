import React, { useState, useEffect, useRef } from 'react';
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
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../store/authContext';
import { authService } from '../../services/authService';
import { useToast } from '../../contexts/ToastContext';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import AnimatedButton from '../../components/common/AnimatedButton';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useSimpleFadeIn, useSimpleSlideIn } from '../../hooks/useSimpleAnimation';

const LoginScreen = ({ navigation }) => {
  const { login } = useAuth();
  const { showSuccess, showError } = useToast();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  
  // Simple animations that won't cause re-render loops
  const titleAnimation = useSimpleFadeIn(300, 0);
  const formAnimation = useSimpleSlideIn(400, 200);
  const buttonAnimation = useSimpleSlideIn(400, 400);

  useEffect(() => {
    checkBiometric();
  }, []);

  const checkBiometric = async () => {
    const { available } = await authService.checkBiometricAvailability();
    setBiometricAvailable(available);
  };

  const handleLogin = async () => {
    console.log('Login button pressed'); // Debug log
    if (!username.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter username and password');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Attempting login with:', username); // Debug log
      const result = await login(username, password);
      if (!result.success) {
        showError(result.error || 'Login failed');
      } else {
        showSuccess('Welcome back!');
      }
      // Navigation will be handled by auth state change
    } catch (error) {
      console.error('Login error:', error); // Debug log
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
        <Animated.View style={[styles.header, titleAnimation]}>
          <View style={styles.iconContainer}>
            <Icon name="assignment-turned-in" size={80} color={colors.primary} />
          </View>
          <Text style={styles.title}>Chores Tracker</Text>
          <Text style={styles.subtitle}>Login to continue</Text>
        </Animated.View>

        <Animated.View style={[styles.form, formAnimation]}>
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

          <Animated.View style={buttonAnimation}>
            <AnimatedButton
              title={isLoading ? 'Logging in...' : 'Login'}
              onPress={handleLogin}
              variant="primary"
              disabled={isLoading}
              showLoader={isLoading}
            />
          </Animated.View>

          {biometricAvailable && (
            <Animated.View style={buttonAnimation}>
              <AnimatedButton
                title="Login with Face ID"
                onPress={handleBiometricLogin}
                variant="outline"
                icon="face"
                style={styles.biometricButton}
              />
            </Animated.View>
          )}
        </Animated.View>
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
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
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
    marginTop: 16,
  },
});

export default LoginScreen;
