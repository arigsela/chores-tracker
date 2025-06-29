import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ErrorView = ({ 
  error, 
  onRetry, 
  title = 'Something went wrong',
  icon = 'error-outline',
  retryText = 'Try Again'
}) => {
  const errorMessage = error?.message || error?.toString() || 'An unexpected error occurred';

  return (
    <View style={styles.container}>
      <Icon name={icon} size={64} color={colors.error} />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{errorMessage}</Text>
      
      {onRetry && (
        <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
          <Icon name="refresh" size={20} color={colors.white} />
          <Text style={styles.retryText}>{retryText}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  title: {
    ...typography.h3,
    color: colors.text,
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  message: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    ...typography.button,
    color: colors.white,
    marginLeft: 8,
  },
});

export default ErrorView;