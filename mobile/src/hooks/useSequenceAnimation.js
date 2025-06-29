import { useRef, useCallback } from 'react';
import { Animated } from 'react-native';

export const useSequenceAnimation = () => {
  const animations = useRef([]).current;

  const addAnimation = useCallback((animation) => {
    animations.push(animation);
  }, [animations]);

  const createFadeSequence = useCallback((items, staggerDelay = 100, duration = 300) => {
    return items.map((_, index) => {
      const fadeValue = new Animated.Value(0);
      
      return {
        fadeValue,
        style: { opacity: fadeValue },
        startAnimation: () => {
          Animated.timing(fadeValue, {
            toValue: 1,
            duration,
            delay: index * staggerDelay,
            useNativeDriver: true,
          }).start();
        },
      };
    });
  }, []);

  const createSlideSequence = useCallback((items, direction = 'up', staggerDelay = 100, duration = 300) => {
    return items.map((_, index) => {
      const slideValue = new Animated.Value(30);
      const fadeValue = new Animated.Value(0);
      
      const transform = direction === 'up' || direction === 'down' 
        ? [{ translateY: slideValue }]
        : [{ translateX: slideValue }];

      return {
        slideValue,
        fadeValue,
        style: {
          opacity: fadeValue,
          transform,
        },
        startAnimation: () => {
          Animated.parallel([
            Animated.timing(slideValue, {
              toValue: 0,
              duration,
              delay: index * staggerDelay,
              useNativeDriver: true,
            }),
            Animated.timing(fadeValue, {
              toValue: 1,
              duration,
              delay: index * staggerDelay,
              useNativeDriver: true,
            }),
          ]).start();
        },
      };
    });
  }, []);

  const createScaleSequence = useCallback((items, staggerDelay = 100, duration = 300) => {
    return items.map((_, index) => {
      const scaleValue = new Animated.Value(0);
      const fadeValue = new Animated.Value(0);

      return {
        scaleValue,
        fadeValue,
        style: {
          opacity: fadeValue,
          transform: [{ scale: scaleValue }],
        },
        startAnimation: () => {
          Animated.parallel([
            Animated.spring(scaleValue, {
              toValue: 1,
              tension: 50,
              friction: 7,
              delay: index * staggerDelay,
              useNativeDriver: true,
            }),
            Animated.timing(fadeValue, {
              toValue: 1,
              duration,
              delay: index * staggerDelay,
              useNativeDriver: true,
            }),
          ]).start();
        },
      };
    });
  }, []);

  const startSequence = useCallback((animationSequence) => {
    animationSequence.forEach(item => {
      if (item.startAnimation) {
        item.startAnimation();
      }
    });
  }, []);

  const createListEnterAnimation = useCallback((items, type = 'slide') => {
    switch (type) {
      case 'fade':
        return createFadeSequence(items);
      case 'scale':
        return createScaleSequence(items);
      case 'slide':
      default:
        return createSlideSequence(items);
    }
  }, [createFadeSequence, createScaleSequence, createSlideSequence]);

  return {
    addAnimation,
    createFadeSequence,
    createSlideSequence,
    createScaleSequence,
    createListEnterAnimation,
    startSequence,
  };
};

export default useSequenceAnimation;