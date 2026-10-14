import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import DashboardScreen from './screens/DashboardScreen';
import WorkoutScreen from './screens/WorkoutScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" backgroundColor="#FAF6F0" />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#FAF6F0',
            borderTopColor: '#EDE8E0',
            borderTopWidth: 1,
          },
          tabBarActiveTintColor: '#C4965A',
          tabBarInactiveTintColor: '#B0A898',
        }}
      >
        <Tab.Screen name="Dashboard" component={DashboardScreen} />
        <Tab.Screen name="Workout" component={WorkoutScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}