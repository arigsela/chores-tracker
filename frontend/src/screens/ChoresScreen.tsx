import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';

export const ChoresScreen: React.FC = () => {
  const { user } = useAuth();
  const isParent = user?.role === 'parent';

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Chores</Text>
      <Text style={styles.subtitle}>
        {isParent ? 'Manage family chores' : 'View your assigned chores'}
      </Text>
      
      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>
          Coming soon in Phase 3 & 4
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