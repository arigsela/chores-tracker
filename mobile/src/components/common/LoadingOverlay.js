import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, ActivityIndicator } from 'react-native';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const LoadingOverlay = ({ 
  visible, 
  message = 'Loading...', 
  transparent = false,
  showSpinner = true,
}) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 0.8,
          duration: 150,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View 
      style={[
        styles.overlay,
        {
          backgroundColor: transparent ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.7)',
          opacity: fadeAnim,
        },
      ]}
    >
      <Animated.View 
        style={[
          styles.container,
          {
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        {showSpinner && (
          <ActivityIndicator 
            size="large" 
            color={colors.primary} 
            style={styles.spinner}
          />
        )}
        <Text style={styles.message}>{message}</Text>
      </Animated.View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
  },
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    minWidth: 120,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  spinner: {
    marginBottom: 12,
  },
  message: {
    ...typography.body,
    color: colors.text,
    textAlign: 'center',
  },
});

export default LoadingOverlay;