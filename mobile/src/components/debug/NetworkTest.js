import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import axios from 'axios';
import { colors } from '../../styles/colors';

const NetworkTest = () => {
  const testConnection = async () => {
    const testUrl = 'http://192.168.0.250:8000/api/v1/openapi.json';
    console.log('Testing connection to:', testUrl);
    
    try {
      const response = await axios.get(testUrl, {
        timeout: 5000,
      });
      console.log('Success! Response status:', response.status);
      Alert.alert('Success', `Connected! Status: ${response.status}`);
    } catch (error) {
      console.error('Network test failed:', error);
      console.error('Error code:', error.code);
      console.error('Error message:', error.message);
      
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      }
      
      Alert.alert(
        'Connection Failed',
        `Error: ${error.message}\nCode: ${error.code}\nURL: ${testUrl}`
      );
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.button} onPress={testConnection}>
        <Text style={styles.buttonText}>Test Network Connection</Text>
      </TouchableOpacity>
      <Text style={styles.info}>Target: http://192.168.0.250:8000</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: colors.warning,
    margin: 10,
    borderRadius: 8,
  },
  button: {
    backgroundColor: colors.primary,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  info: {
    marginTop: 10,
    textAlign: 'center',
    fontSize: 12,
  },
});

export default NetworkTest;