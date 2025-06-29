import React, { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet } from 'react-native';
import { colors } from '../../styles/colors';

const SkeletonPlaceholder = ({ width, height, borderRadius = 4, style }) => {
  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(animatedValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(animatedValue, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [animatedValue]);

  const opacity = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
          opacity,
        },
        style,
      ]}
    />
  );
};

export const SkeletonCard = ({ style }) => (
  <View style={[styles.card, style]}>
    <View style={styles.cardHeader}>
      <SkeletonPlaceholder width={120} height={20} />
      <SkeletonPlaceholder width={60} height={20} borderRadius={10} />
    </View>
    <SkeletonPlaceholder width="80%" height={16} style={{ marginTop: 8 }} />
    <View style={styles.cardFooter}>
      <SkeletonPlaceholder width={80} height={16} />
      <SkeletonPlaceholder width={40} height={16} />
    </View>
  </View>
);

export const SkeletonList = ({ count = 3, renderItem }) => (
  <View>
    {Array.from({ length: count }).map((_, index) => (
      <View key={index}>
        {renderItem ? renderItem() : <SkeletonCard />}
      </View>
    ))}
  </View>
);

export const SkeletonText = ({ lines = 1, width = '100%', style }) => (
  <View style={style}>
    {Array.from({ length: lines }).map((_, index) => (
      <SkeletonPlaceholder
        key={index}
        width={index === lines - 1 ? '60%' : width}
        height={16}
        style={{ marginBottom: index < lines - 1 ? 8 : 0 }}
      />
    ))}
  </View>
);

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: colors.border,
  },
  card: {
    backgroundColor: colors.surface,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
});

export default SkeletonPlaceholder;