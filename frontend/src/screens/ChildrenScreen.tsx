import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const ChildrenScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>My Children</Text>
      <Text style={styles.subtitle}>
        Manage your children's accounts and view their progress
      </Text>
      
      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>
          Coming soon in Phase 4
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
  },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 18,
    color: '#999',
  },
});