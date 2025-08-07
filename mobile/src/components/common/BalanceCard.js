import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { useAuth } from '../../store/authContext';

const BalanceCard = ({ onRefresh, showDetails = true }) => {
  const { userBalance, refreshBalance } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Animations
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const expandAnim = useRef(new Animated.Value(0)).current;
  
  // Animate on balance change
  useEffect(() => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1.05,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [userBalance]);
  
  const handleRefresh = async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    
    // Rotate refresh icon
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      })
    ).start();
    
    await refreshBalance();
    if (onRefresh) await onRefresh();
    
    setIsRefreshing(false);
    rotateAnim.stopAnimation();
    rotateAnim.setValue(0);
  };
  
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    Animated.timing(expandAnim, {
      toValue: isExpanded ? 0 : 1,
      duration: 300,
      useNativeDriver: false,
    }).start();
  };
  
  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });
  
  return (
    <Animated.View style={[styles.container, { transform: [{ scale: scaleAnim }] }]}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Icon name="account-balance-wallet" size={24} color={colors.primary} />
          <Text style={styles.title}>My Balance</Text>
          <TouchableOpacity onPress={handleRefresh} disabled={isRefreshing}>
            <Animated.View style={{ transform: [{ rotate: rotateInterpolate }] }}>
              <Icon 
                name="refresh" 
                size={20} 
                color={isRefreshing ? colors.textSecondary : colors.primary} 
              />
            </Animated.View>
          </TouchableOpacity>
        </View>
        
        <Text style={styles.balance}>
          ${(userBalance || 0).toFixed(2)}
        </Text>
        
        {showDetails && (
          <TouchableOpacity onPress={toggleExpanded} style={styles.expandButton}>
            <Text style={styles.expandText}>
              {isExpanded ? 'Hide' : 'Show'} Details
            </Text>
            <Icon 
              name={isExpanded ? 'expand-less' : 'expand-more'} 
              size={20} 
              color={colors.primary} 
            />
          </TouchableOpacity>
        )}
      </View>
      
      {showDetails && (
        <Animated.View 
          style={[
            styles.details,
            {
              maxHeight: expandAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, 200],
              }),
              opacity: expandAnim,
            },
          ]}
        >
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Earned from chores:</Text>
            <Text style={styles.detailValue}>$0.00</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Adjustments:</Text>
            <Text style={styles.detailValue}>$0.00</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Paid out:</Text>
            <Text style={[styles.detailValue, styles.negative]}>$0.00</Text>
          </View>
          <View style={[styles.detailRow, styles.totalRow]}>
            <Text style={styles.detailLabel}>Current balance:</Text>
            <Text style={styles.totalValue}>${(userBalance || 0).toFixed(2)}</Text>
          </View>
        </Animated.View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    alignItems: 'center',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    ...typography.body1,
    color: colors.text,
    marginHorizontal: 8,
    flex: 1,
  },
  balance: {
    ...typography.h1,
    color: colors.primary,
    fontSize: 36,
    fontWeight: 'bold',
    marginVertical: 8,
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  expandText: {
    ...typography.caption,
    color: colors.primary,
    marginRight: 4,
  },
  details: {
    overflow: 'hidden',
    marginTop: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  detailLabel: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  detailValue: {
    ...typography.body2,
    color: colors.text,
    fontWeight: '500',
  },
  negative: {
    color: colors.error,
  },
  totalRow: {
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    marginTop: 8,
    paddingTop: 12,
  },
  totalValue: {
    ...typography.body1,
    color: colors.primary,
    fontWeight: 'bold',
  },
});

export default BalanceCard;