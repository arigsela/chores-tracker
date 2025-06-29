import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const NetworkStatusBar = () => {
  const [isConnected, setIsConnected] = useState(true);
  const [isVisible, setIsVisible] = useState(false);
  const animatedHeight = new Animated.Value(0);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const connected = state.isConnected && state.isInternetReachable;
      setIsConnected(connected);
      setIsVisible(!connected);
    });

    // Check initial state
    NetInfo.fetch().then(state => {
      const connected = state.isConnected && state.isInternetReachable;
      setIsConnected(connected);
      setIsVisible(!connected);
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    Animated.timing(animatedHeight, {
      toValue: isVisible ? 40 : 0,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [isVisible]);

  if (isConnected && !isVisible) {
    return null;
  }

  return (
    <Animated.View style={[styles.container, { height: animatedHeight }]}>
      <View style={styles.content}>
        <Icon name="wifi-off" size={20} color={colors.white} />
        <Text style={styles.text}>No Internet Connection</Text>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.error,
    overflow: 'hidden',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  text: {
    ...typography.caption,
    color: colors.white,
    marginLeft: 8,
    fontWeight: '600',
  },
});

export default NetworkStatusBar;