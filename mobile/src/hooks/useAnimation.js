import { useRef, useEffect, useCallback } from 'react';
import { Animated } from 'react-native';

export const useAnimation = (initialValue = 0, config = {}) => {
  const animatedValue = useRef(new Animated.Value(initialValue)).current;

  const animate = (toValue, options = {}) => {
    const {
      duration = 300,
      useNativeDriver = true,
      easing,
      onComplete,
    } = options;

    return Animated.timing(animatedValue, {
      toValue,
      duration,
      useNativeDriver,
      easing,
    }).start(onComplete);
  };

  const spring = (toValue, options = {}) => {
    const {
      tension = 40,
      friction = 7,
      useNativeDriver = true,
      onComplete,
    } = options;

    return Animated.spring(animatedValue, {
      toValue,
      tension,
      friction,
      useNativeDriver,
    }).start(onComplete);
  };

  return {
    value: animatedValue,
    animate,
    spring,
  };
};

export const useFadeIn = (delay = 0) => {
  const opacity = useRef(new Animated.Value(0)).current;
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true;
      const timer = setTimeout(() => {
        Animated.timing(opacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();
      }, delay);

      return () => clearTimeout(timer);
    }
  }, [delay]);

  return { opacity };
};

export const useSlideIn = (delay = 0, direction = 'up') => {
  const translateValue = useRef(new Animated.Value(direction === 'up' ? 30 : -30)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true;
      const timer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(translateValue, {
            toValue: 0,
            duration: 400,
            useNativeDriver: true,
          }),
          Animated.timing(opacity, {
            toValue: 1,
            duration: 400,
            useNativeDriver: true,
          }),
        ]).start();
      }, delay);

      return () => clearTimeout(timer);
    }
  }, [delay, direction]);

  return {
    opacity,
    transform: [{ translateY: translateValue }],
  };
};

export const useScalePress = () => {
  const scale = useRef(new Animated.Value(1)).current;

  const onPressIn = useCallback(() => {
    Animated.spring(scale, {
      toValue: 0.95,
      useNativeDriver: true,
    }).start();
  }, [scale]);

  const onPressOut = useCallback(() => {
    Animated.spring(scale, {
      toValue: 1,
      useNativeDriver: true,
    }).start();
  }, [scale]);

  return {
    scale,
    onPressIn,
    onPressOut,
  };
};