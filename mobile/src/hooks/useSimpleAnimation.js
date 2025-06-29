import { useRef, useEffect } from 'react';
import { Animated } from 'react-native';

// Simple fade in hook without dependencies that could cause re-renders
export const useSimpleFadeIn = (duration = 300, delay = 0) => {
  const opacity = useRef(new Animated.Value(0)).current;
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true;
      
      const timer = setTimeout(() => {
        Animated.timing(opacity, {
          toValue: 1,
          duration,
          useNativeDriver: true,
        }).start();
      }, delay);

      return () => clearTimeout(timer);
    }
  }, []); // Empty dependency array - only run once

  return { opacity };
};

// Simple slide and fade hook
export const useSimpleSlideIn = (duration = 400, delay = 0) => {
  const translateY = useRef(new Animated.Value(30)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true;
      
      const timer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(translateY, {
            toValue: 0,
            duration,
            useNativeDriver: true,
          }),
          Animated.timing(opacity, {
            toValue: 1,
            duration,
            useNativeDriver: true,
          }),
        ]).start();
      }, delay);

      return () => clearTimeout(timer);
    }
  }, []); // Empty dependency array - only run once

  return {
    opacity,
    transform: [{ translateY }],
  };
};

export default { useSimpleFadeIn, useSimpleSlideIn };