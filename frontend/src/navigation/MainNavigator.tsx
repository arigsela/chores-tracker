import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MainStackParamList, MainTabParamList } from './types';
import { useAuth } from '@/contexts/AuthContext';
import { HomeScreen } from '@/screens/HomeScreen';
import { ChoresScreen } from '@/screens/ChoresScreen';
import { ChildrenScreen } from '@/screens/ChildrenScreen';
import { BalanceScreen } from '@/screens/BalanceScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import FamilySettingsScreen from '@/screens/FamilySettingsScreen';
import JoinFamilyScreen from '@/screens/JoinFamilyScreen';
import { Text } from 'react-native';

const Stack = createNativeStackNavigator<MainStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

const TabNavigator: React.FC = () => {
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

export const MainNavigator: React.FC = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen 
        name="TabNavigator" 
        component={TabNavigator} 
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="FamilySettings" 
        component={FamilySettingsScreen}
        options={{
          title: 'Family Settings',
          headerStyle: { backgroundColor: '#007AFF' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      />
      <Stack.Screen 
        name="JoinFamily" 
        component={JoinFamilyScreen}
        options={{
          title: 'Join Family',
          headerStyle: { backgroundColor: '#007AFF' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      />
    </Stack.Navigator>
  );
};