import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { LoginScreen } from '@/screens/LoginScreen';
import { RegisterScreen } from '@/screens/RegisterScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { ChoresScreen } from '@/screens/ChoresScreen';
import { ChildrenScreen } from '@/screens/ChildrenScreen';
import { BalanceScreen } from '@/screens/BalanceScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import ApprovalsScreen from '@/screens/ApprovalsScreen';
import { AllowanceSummaryScreen } from '@/screens/AllowanceSummaryScreen';
import { StatisticsScreen } from '@/screens/StatisticsScreen';
import { FamilySettingsScreen } from '@/screens/FamilySettingsScreen';

type TabName = 'Home' | 'Chores' | 'Children' | 'Approvals' | 'Balance' | 'Profile' | 'Reports' | 'Statistics' | 'FamilySettings';
type AuthScreen = 'login' | 'register';

export const SimpleNavigator: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabName>('Home');
  const [authScreen, setAuthScreen] = useState<AuthScreen>('login');
  
  if (!isAuthenticated) {
    if (authScreen === 'register') {
      return <RegisterScreen onBackToLogin={() => setAuthScreen('login')} />;
    }
    return <LoginScreen onNavigateToRegister={() => setAuthScreen('register')} />;
  }

  const isParent = user?.role === 'parent';

  const renderScreen = () => {
    switch (activeTab) {
      case 'Home':
        return <HomeScreen onNavigate={setActiveTab} />;
      case 'Chores':
        return <ChoresScreen />;
      case 'Children':
        return isParent ? <ChildrenScreen /> : <BalanceScreen />;
      case 'Approvals':
        return isParent ? <ApprovalsScreen /> : <BalanceScreen />;
      case 'Reports':
        return isParent ? <AllowanceSummaryScreen /> : <BalanceScreen />;
      case 'Statistics':
        return isParent ? <StatisticsScreen /> : <BalanceScreen />;
      case 'Balance':
        return <BalanceScreen />;
      case 'Profile':
        return <ProfileScreen onNavigate={setActiveTab} />;
      case 'FamilySettings':
        return <FamilySettingsScreen onNavigate={setActiveTab} />;
      default:
        return <HomeScreen onNavigate={setActiveTab} />;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Chores Tracker</Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {renderScreen()}
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'Home' && styles.activeTab]}
          onPress={() => setActiveTab('Home')}
        >
          <Text style={styles.tabIcon}>🏠</Text>
          <Text style={[styles.tabLabel, activeTab === 'Home' && styles.activeTabLabel]}>
            Home
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'Chores' && styles.activeTab]}
          onPress={() => setActiveTab('Chores')}
        >
          <Text style={styles.tabIcon}>✅</Text>
          <Text style={[styles.tabLabel, activeTab === 'Chores' && styles.activeTabLabel]}>
            Chores
          </Text>
        </TouchableOpacity>

        {isParent ? (
          <>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'Children' && styles.activeTab]}
              onPress={() => setActiveTab('Children')}
            >
              <Text style={styles.tabIcon}>👨‍👩‍👧‍👦</Text>
              <Text style={[styles.tabLabel, activeTab === 'Children' && styles.activeTabLabel]}>
                Children
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.tab, activeTab === 'Approvals' && styles.activeTab]}
              onPress={() => setActiveTab('Approvals')}
            >
              <Text style={styles.tabIcon}>✔️</Text>
              <Text style={[styles.tabLabel, activeTab === 'Approvals' && styles.activeTabLabel]}>
                Approvals
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.tab, activeTab === 'Reports' && styles.activeTab]}
              onPress={() => setActiveTab('Reports')}
            >
              <Text style={styles.tabIcon}>📊</Text>
              <Text style={[styles.tabLabel, activeTab === 'Reports' && styles.activeTabLabel]}>
                Reports
              </Text>
            </TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity
            style={[styles.tab, activeTab === 'Balance' && styles.activeTab]}
            onPress={() => setActiveTab('Balance')}
          >
            <Text style={styles.tabIcon}>💰</Text>
            <Text style={[styles.tabLabel, activeTab === 'Balance' && styles.activeTabLabel]}>
              Balance
            </Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={[styles.tab, activeTab === 'Profile' && styles.activeTab]}
          onPress={() => setActiveTab('Profile')}
        >
          <Text style={styles.tabIcon}>👤</Text>
          <Text style={[styles.tabLabel, activeTab === 'Profile' && styles.activeTabLabel]}>
            Profile
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 20,
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingVertical: 5,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
  },
  activeTab: {
    borderTopWidth: 2,
    borderTopColor: '#007AFF',
  },
  tabIcon: {
    fontSize: 24,
    marginBottom: 2,
  },
  tabLabel: {
    fontSize: 10,
    color: '#999',
  },
  activeTabLabel: {
    color: '#007AFF',
    fontWeight: '600',
  },
});