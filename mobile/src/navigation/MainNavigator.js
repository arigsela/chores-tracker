import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuth } from '../store/authContext';
import { Text, View } from 'react-native';
import { colors } from '../styles/colors';

const Tab = createBottomTabNavigator();

// Temporary placeholder screens
const ParentHomeScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Parent Home Screen</Text>
  </View>
);

const ChildHomeScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Child Home Screen</Text>
  </View>
);

const ProfileScreen = () => {
  const { user, logout } = useAuth();
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Text>Welcome, {user?.username}!</Text>
      <Text>Role: {user?.role}</Text>
      <Text onPress={logout} style={{ color: colors.primary, marginTop: 20 }}>
        Logout
      </Text>
    </View>
  );
};

const MainNavigator = () => {
  const { isParent } = useAuth();

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        headerShown: true,
      }}
    >
      <Tab.Screen
        name="Home"
        component={isParent ? ParentHomeScreen : ChildHomeScreen}
        options={{ title: 'Chores' }}
      />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
};

export default MainNavigator;
