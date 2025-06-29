import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../styles/colors';
import { typography } from '../styles/typography';

const SplashScreen = () => {
  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <View style={styles.iconBackground}>
          <Icon name="assignment-turned-in" size={80} color={colors.white} />
        </View>
        <Text style={styles.title}>Chores Tracker</Text>
        <Text style={styles.subtitle}>Family Task Management</Text>
      </View>
      <ActivityIndicator size="large" color={colors.primary} style={styles.loader} />
      <Text style={styles.loadingText}>Loading...</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 50,
  },
  iconBackground: {
    width: 120,
    height: 120,
    borderRadius: 30,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  title: {
    ...typography.h1,
    color: colors.primary,
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    fontSize: 16,
  },
  loader: {
    marginTop: 50,
  },
  loadingText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 10,
  },
});

export default SplashScreen;