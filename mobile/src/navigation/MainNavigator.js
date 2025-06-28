import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { useAuth } from '../store/authContext';
import { Text, View, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../styles/colors';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Import screens
import ParentHomeScreen from '../screens/parent/ParentHomeScreen';
import ChildHomeScreen from '../screens/child/ChildHomeScreen';
import CreateChoreScreen from '../screens/parent/CreateChoreScreen';
import ApprovalQueueScreen from '../screens/parent/ApprovalQueueScreen';

const ChildManagementScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Child Management Screen</Text>
  </View>
);

import RewardsScreen from '../screens/child/RewardsScreen';

const ProfileScreen = () => {
  const { user, logout } = useAuth();
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
      <Icon name="account-circle" size={80} color={colors.primary} />
      <Text style={{ fontSize: 24, marginTop: 10 }}>Welcome, {user?.username}!</Text>
      <Text style={{ fontSize: 16, color: colors.textSecondary }}>
        Role: {user?.is_parent ? 'Parent' : 'Child'}
      </Text>
      <TouchableOpacity
        onPress={logout}
        style={{
          marginTop: 30,
          paddingHorizontal: 30,
          paddingVertical: 10,
          backgroundColor: colors.error,
          borderRadius: 5,
        }}
      >
        <Text style={{ color: 'white', fontSize: 16 }}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
};

// Stack Navigators for each tab
const HomeStack = createStackNavigator();
const HomeStackScreen = ({ isParent }) => (
  <HomeStack.Navigator>
    <HomeStack.Screen
      name="HomeMain"
      component={isParent ? ParentHomeScreen : ChildHomeScreen}
      options={{ title: 'Chores' }}
    />
  </HomeStack.Navigator>
);

const CreateStack = createStackNavigator();
const CreateStackScreen = () => (
  <CreateStack.Navigator>
    <CreateStack.Screen
      name="CreateMain"
      component={CreateChoreScreen}
      options={{ title: 'Create Chore' }}
    />
  </CreateStack.Navigator>
);

const ApprovalsStack = createStackNavigator();
const ApprovalsStackScreen = () => (
  <ApprovalsStack.Navigator>
    <ApprovalsStack.Screen
      name="ApprovalsMain"
      component={ApprovalQueueScreen}
      options={{ title: 'Approvals' }}
    />
  </ApprovalsStack.Navigator>
);

const FamilyStack = createStackNavigator();
const FamilyStackScreen = () => (
  <FamilyStack.Navigator>
    <FamilyStack.Screen
      name="FamilyMain"
      component={ChildManagementScreen}
      options={{ title: 'Family' }}
    />
  </FamilyStack.Navigator>
);

const RewardsStack = createStackNavigator();
const RewardsStackScreen = () => (
  <RewardsStack.Navigator>
    <RewardsStack.Screen
      name="RewardsMain"
      component={RewardsScreen}
      options={{ title: 'My Rewards' }}
    />
  </RewardsStack.Navigator>
);

// Parent Navigator
const ParentNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;
        switch (route.name) {
          case 'Home':
            iconName = 'home';
            break;
          case 'Create':
            iconName = 'add-circle';
            break;
          case 'Approvals':
            iconName = 'check-circle';
            break;
          case 'Family':
            iconName = 'people';
            break;
          case 'Profile':
            iconName = 'person';
            break;
          default:
            iconName = 'circle';
        }
        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.textSecondary,
      headerShown: false,
    })}
  >
    <Tab.Screen name="Home" options={{ title: 'Chores' }}>
      {() => <HomeStackScreen isParent={true} />}
    </Tab.Screen>
    <Tab.Screen name="Create" component={CreateStackScreen} />
    <Tab.Screen name="Approvals" component={ApprovalsStackScreen} />
    <Tab.Screen name="Family" component={FamilyStackScreen} />
    <Tab.Screen name="Profile" component={ProfileScreen} />
  </Tab.Navigator>
);

// Child Navigator
const ChildNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;
        switch (route.name) {
          case 'Home':
            iconName = 'home';
            break;
          case 'Rewards':
            iconName = 'star';
            break;
          case 'Profile':
            iconName = 'person';
            break;
          default:
            iconName = 'circle';
        }
        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.textSecondary,
      headerShown: false,
    })}
  >
    <Tab.Screen name="Home" options={{ title: 'My Chores' }}>
      {() => <HomeStackScreen isParent={false} />}
    </Tab.Screen>
    <Tab.Screen name="Rewards" component={RewardsStackScreen} />
    <Tab.Screen name="Profile" component={ProfileScreen} />
  </Tab.Navigator>
);

const MainNavigator = () => {
  const { user } = useAuth();
  const isParent = user?.is_parent || false;

  return isParent ? <ParentNavigator /> : <ChildNavigator />;
};

export default MainNavigator;
