import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider } from 'react-native-paper';
import { QueryClient, QueryClientProvider } from 'react-query';
import Toast from 'react-native-toast-message';
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';
import * as Notifications from 'expo-notifications';
import { Ionicons } from '@expo/vector-icons';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ProjectsScreen from './src/screens/ProjectsScreen';
import ProjectDetailScreen from './src/screens/ProjectDetailScreen';
import WorkflowsScreen from './src/screens/WorkflowsScreen';
import WorkflowBuilderScreen from './src/screens/WorkflowBuilderScreen';
import MarketplaceScreen from './src/screens/MarketplaceScreen';
import ConsultantsScreen from './src/screens/ConsultantsScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';

// Services
import { AuthService } from './src/services/AuthService';
import { NotificationService } from './src/services/NotificationService';
import { OfflineService } from './src/services/OfflineService';

// Theme
import { theme } from './src/theme/theme';

// Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Login: undefined;
  Register: undefined;
  ProjectDetail: { projectId: number };
  WorkflowBuilder: { workflowId?: number; projectId: number };
};

export type MainTabParamList = {
  Dashboard: undefined;
  Projects: undefined;
  Workflows: undefined;
  Marketplace: undefined;
  Consultants: undefined;
  Analytics: undefined;
  Profile: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();
const queryClient = new QueryClient();

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          switch (route.name) {
            case 'Dashboard':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Projects':
              iconName = focused ? 'folder' : 'folder-outline';
              break;
            case 'Workflows':
              iconName = focused ? 'git-network' : 'git-network-outline';
              break;
            case 'Marketplace':
              iconName = focused ? 'storefront' : 'storefront-outline';
              break;
            case 'Consultants':
              iconName = focused ? 'people' : 'people-outline';
              break;
            case 'Analytics':
              iconName = focused ? 'analytics' : 'analytics-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Projects" component={ProjectsScreen} />
      <Tab.Screen name="Workflows" component={WorkflowsScreen} />
      <Tab.Screen name="Marketplace" component={MarketplaceScreen} />
      <Tab.Screen name="Consultants" component={ConsultantsScreen} />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize services
      await NotificationService.initialize();
      await OfflineService.initialize();

      // Check authentication status
      const token = await SecureStore.getItemAsync('authToken');
      if (token) {
        // Verify token validity
        const isValid = await AuthService.verifyToken(token);
        setIsAuthenticated(isValid);
      } else {
        setIsAuthenticated(false);
      }

      // Setup biometric authentication if available
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      
      if (hasHardware && isEnrolled) {
        const biometricEnabled = await SecureStore.getItemAsync('biometricEnabled');
        if (biometricEnabled === 'true') {
          const result = await LocalAuthentication.authenticateAsync({
            promptMessage: 'Authenticate to access AI Platform',
            fallbackLabel: 'Use passcode',
          });
          
          if (!result.success) {
            setIsAuthenticated(false);
          }
        }
      }

    } catch (error) {
      console.error('App initialization error:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return null; // Show splash screen
  }

  return (
    <QueryClientProvider client={queryClient}>
      <PaperProvider theme={theme}>
        <NavigationContainer>
          <StatusBar style="auto" />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            {isAuthenticated ? (
              <>
                <Stack.Screen name="Main" component={MainTabs} />
                <Stack.Screen 
                  name="ProjectDetail" 
                  component={ProjectDetailScreen}
                  options={{ headerShown: true, title: 'Project Details' }}
                />
                <Stack.Screen 
                  name="WorkflowBuilder" 
                  component={WorkflowBuilderScreen}
                  options={{ headerShown: true, title: 'Workflow Builder' }}
                />
              </>
            ) : (
              <Stack.Screen name="Auth" component={AuthStack} />
            )}
          </Stack.Navigator>
          <Toast />
        </NavigationContainer>
      </PaperProvider>
    </QueryClientProvider>
  );
}
