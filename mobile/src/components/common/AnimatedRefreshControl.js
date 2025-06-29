import React, { useRef, useEffect } from 'react';
import { RefreshControl, Animated } from 'react-native';
import { colors } from '../../styles/colors';

const AnimatedRefreshControl = ({ refreshing, onRefresh, ...props }) => {
  const rotation = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    if (refreshing) {
      // Start rotation animation
      Animated.loop(
        Animated.timing(rotation, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        })
      ).start();
    } else {
      // Reset rotation
      rotation.setValue(0);
    }
  }, [refreshing, rotation]);

  return (
    <RefreshControl
      refreshing={refreshing}
      onRefresh={onRefresh}
      colors={[colors.primary, colors.secondary]}
      tintColor={colors.primary}
      progressBackgroundColor={colors.surface}
      {...props}
    />
  );
};

export default AnimatedRefreshControl;