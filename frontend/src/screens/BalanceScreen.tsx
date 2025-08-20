import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { balanceAPI, UserBalance } from '@/api/balance';

export const BalanceScreen: React.FC = () => {
  const { user } = useAuth();
  const isParent = user?.role === 'parent';
  
  const [balance, setBalance] = useState<UserBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchBalance = async (refresh = false) => {
    try {
      if (refresh) setIsRefreshing(true);
      else setIsLoading(true);

      if (isParent) {
        // Parents see a different view - for now just show a message
        // In Phase 4, we'll implement the parent's children summary view
        setBalance(null);
      } else {
        const balanceData = await balanceAPI.getMyBalance();
        
        // DEBUG: Log the raw balance API response
        console.log('[BALANCE AUDIT] Raw balance API response:', JSON.stringify(balanceData, null, 2));
        
        // Calculate manual sum for verification
        const manualBalance = balanceData.total_earned + balanceData.adjustments - balanceData.paid_out;
        console.log('[BALANCE AUDIT] Manual calculation:', {
          total_earned: balanceData.total_earned,
          adjustments: balanceData.adjustments,
          paid_out: balanceData.paid_out,
          manual_sum: manualBalance,
          api_balance: balanceData.balance,
          difference: balanceData.balance - manualBalance
        });
        
        setBalance(balanceData);
      }
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      if (!refresh) {
        Alert.alert('Error', 'Failed to load balance. Please try again.');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  const formatCurrency = (amount: number) => {
    return `$${amount.toFixed(2)}`;
  };

  const renderBalanceCard = (title: string, amount: number, color: string, description?: string) => (
    <View style={[styles.card, { borderLeftColor: color }]}>
      <Text style={styles.cardTitle}>{title}</Text>
      <Text style={[styles.cardAmount, { color }]}>{formatCurrency(amount)}</Text>
      {description && <Text style={styles.cardDescription}>{description}</Text>}
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (isParent) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Family Balances</Text>
          <Text style={styles.subtitle}>View your children's earnings</Text>
        </View>
        <View style={styles.centerContainer}>
          <Text style={styles.placeholderText}>
            Children's balance summary will be available in Phase 4
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={() => fetchBalance(true)} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>My Balance</Text>
          <Text style={styles.subtitle}>Track your earnings and rewards</Text>
        </View>

        {balance && (
          <>
            {/* Main Balance */}
            <View style={styles.mainBalanceCard}>
              <Text style={styles.mainBalanceLabel}>Current Balance</Text>
              <Text style={styles.mainBalanceAmount}>
                {formatCurrency(balance.balance)}
              </Text>
              <Text style={styles.mainBalanceFormula}>
                Earned + Bonuses - Paid Out
              </Text>
            </View>

            {/* Balance Details */}
            <View style={styles.detailsSection}>
              <Text style={styles.sectionTitle}>Balance Details</Text>
              
              {renderBalanceCard(
                'Total Earned',
                balance.total_earned,
                '#34C759',
                'From completed and approved chores'
              )}
              
              {renderBalanceCard(
                'Adjustments',
                balance.adjustments,
                balance.adjustments >= 0 ? '#007AFF' : '#FF3B30',
                'Bonuses or deductions from parents'
              )}
              
              {renderBalanceCard(
                'Paid Out',
                balance.paid_out,
                '#8E8E93',
                'Amount already received'
              )}
              
              {balance.pending_chores_value > 0 && renderBalanceCard(
                'Pending Approval',
                balance.pending_chores_value,
                '#FF9500',
                'Waiting for parent approval'
              )}
            </View>

            {/* Summary */}
            <View style={styles.summarySection}>
              <Text style={styles.summaryText}>
                {balance.pending_chores_value > 0
                  ? `You have ${formatCurrency(balance.pending_chores_value)} pending approval. Once approved, it will be added to your balance.`
                  : balance.balance > 0
                  ? `Great job! You've earned ${formatCurrency(balance.balance)}. Keep up the good work!`
                  : 'Complete chores to start earning rewards!'}
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  mainBalanceCard: {
    backgroundColor: '#007AFF',
    margin: 20,
    padding: 30,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  mainBalanceLabel: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
    marginBottom: 8,
  },
  mainBalanceAmount: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  mainBalanceFormula: {
    fontSize: 12,
    color: '#fff',
    opacity: 0.7,
  },
  detailsSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  cardAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 12,
    color: '#999',
  },
  summarySection: {
    padding: 20,
    marginTop: 10,
  },
  summaryText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
  placeholderText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
});