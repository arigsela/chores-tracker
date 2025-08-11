import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MainTabParamList } from './types';
import { useAuth } from '@/contexts/AuthContext';
import { HomeScreen } from '@/screens/HomeScreen';
import { ChoresScreen } from '@/screens/ChoresScreen';
import { ChildrenScreen } from '@/screens/ChildrenScreen';
import { BalanceScreen } from '@/screens/BalanceScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { Text } from 'react-native';

const Tab = createBottomTabNavigator<MainTabParamList>();

export const MainNavigator: React.FC = () => {
  const { user } = useAuth();
  const isParent = user?.role === 'parent';

  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#007AFF',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
      }}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          title: 'Dashboard',
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ color, fontSize: size }}>🏠</Text>
          ),
        }}
      />
      
      <Tab.Screen 
        name="Chores" 
        component={ChoresScreen}
        options={{
          title: 'Chores',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ color, fontSize: size }}>✅</Text>
          ),
        }}
      />
      
      {isParent ? (
        <Tab.Screen 
          name="Children" 
          component={ChildrenScreen}
          options={{
            title: 'Children',
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>👨‍👩‍👧‍👦</Text>
            ),
          }}
        />
      ) : (
        <Tab.Screen 
          name="Balance" 
          component={BalanceScreen}
          options={{
            title: 'My Balance',
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>💰</Text>
            ),
          }}
        />
      )}
      
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ color, fontSize: size }}>👤</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
};