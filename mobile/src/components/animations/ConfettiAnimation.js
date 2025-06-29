import React, { useEffect, useRef } from 'react';
import { View, Animated, Dimensions } from 'react-native';
import { colors } from '../../styles/colors';

const { width, height } = Dimensions.get('window');

const ConfettiPiece = ({ color, size, delay }) => {
  const translateY = useRef(new Animated.Value(-50)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const rotate = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const randomX = (Math.random() - 0.5) * width;
    const randomRotation = Math.random() * 360;
    
    setTimeout(() => {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: height + 100,
          duration: 3000 + Math.random() * 2000,
          useNativeDriver: true,
        }),
        Animated.timing(translateX, {
          toValue: randomX,
          duration: 3000 + Math.random() * 2000,
          useNativeDriver: true,
        }),
        Animated.loop(
          Animated.timing(rotate, {
            toValue: randomRotation,
            duration: 1000 + Math.random() * 1000,
            useNativeDriver: true,
          })
        ),
      ]).start();
    }, delay);
  }, []);

  const rotateInterpolate = rotate.interpolate({
    inputRange: [0, 360],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Animated.View
      style={{
        position: 'absolute',
        width: size,
        height: size,
        backgroundColor: color,
        borderRadius: size / 2,
        transform: [
          { translateY },
          { translateX },
          { rotate: rotateInterpolate },
        ],
      }}
    />
  );
};

const ConfettiAnimation = ({ visible, duration = 3000 }) => {
  const confettiColors = [
    colors.primary,
    colors.secondary,
    colors.success,
    colors.warning,
    colors.info,
    '#FF6B6B',
    '#4ECDC4',
    '#45B7D1',
    '#FFA07A',
    '#98D8C8',
  ];

  if (!visible) return null;

  return (
    <View style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      pointerEvents: 'none',
      zIndex: 9998,
    }}>
      {Array.from({ length: 50 }, (_, index) => (
        <ConfettiPiece
          key={index}
          color={confettiColors[Math.floor(Math.random() * confettiColors.length)]}
          size={6 + Math.random() * 8}
          delay={index * 100}
        />
      ))}
    </View>
  );
};

export default ConfettiAnimation;