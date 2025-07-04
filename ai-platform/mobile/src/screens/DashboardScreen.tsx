import React, { useEffect, useState } from 'react';
import {
  View,
  ScrollView,
  RefreshControl,
  StyleSheet,
  Dimensions,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Surface,
  Text,
  IconButton,
  Chip,
} from 'react-native-paper';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from 'react-query';

import { ApiService } from '../services/ApiService';
import { OfflineService } from '../services/OfflineService';
import { theme } from '../theme/theme';

const screenWidth = Dimensions.get('window').width;

interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  ai_services_used: number;
}

interface RecentActivity {
  id: number;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  status: string;
}

export default function DashboardScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery('dashboardStats', ApiService.getDashboardStats, {
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const {
    data: recentActivity,
    isLoading: activityLoading,
    refetch: refetchActivity,
  } = useQuery('recentActivity', ApiService.getRecentActivity, {
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  const {
    data: chartData,
    isLoading: chartLoading,
    refetch: refetchChart,
  } = useQuery('dashboardChart', ApiService.getDashboardChart, {
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  useEffect(() => {
    checkOfflineStatus();
  }, []);

  const checkOfflineStatus = async () => {
    const offline = await OfflineService.isOffline();
    setIsOffline(offline);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchStats(),
        refetchActivity(),
        refetchChart(),
      ]);
    } catch (error) {
      console.error('Refresh error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const renderStatCard = (title: string, value: number, icon: string, color: string) => (
    <Surface style={[styles.statCard, { borderLeftColor: color }]}>
      <View style={styles.statContent}>
        <View style={styles.statHeader}>
          <Ionicons name={icon as any} size={24} color={color} />
          <Text style={styles.statValue}>{value}</Text>
        </View>
        <Text style={styles.statTitle}>{title}</Text>
      </View>
    </Surface>
  );

  const renderActivityItem = (item: RecentActivity) => (
    <Card key={item.id} style={styles.activityCard}>
      <Card.Content>
        <View style={styles.activityHeader}>
          <View style={styles.activityInfo}>
            <Title style={styles.activityTitle}>{item.title}</Title>
            <Paragraph style={styles.activityDescription}>
              {item.description}
            </Paragraph>
          </View>
          <Chip
            mode="outlined"
            style={[
              styles.statusChip,
              {
                backgroundColor:
                  item.status === 'completed'
                    ? theme.colors.success
                    : item.status === 'running'
                    ? theme.colors.warning
                    : theme.colors.error,
              },
            ]}
          >
            {item.status}
          </Chip>
        </View>
        <Text style={styles.timestamp}>
          {new Date(item.timestamp).toLocaleDateString()}
        </Text>
      </Card.Content>
    </Card>
  );

  const chartConfig = {
    backgroundColor: theme.colors.surface,
    backgroundGradientFrom: theme.colors.surface,
    backgroundGradientTo: theme.colors.surface,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(37, 99, 235, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16,
    },
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Title style={styles.welcomeTitle}>Welcome back!</Title>
          <Paragraph style={styles.welcomeSubtitle}>
            Here's what's happening with your AI projects
          </Paragraph>
        </View>
        <IconButton
          icon="bell-outline"
          size={24}
          onPress={() => {/* Navigate to notifications */}}
        />
      </View>

      {/* Offline Indicator */}
      {isOffline && (
        <Surface style={styles.offlineIndicator}>
          <Ionicons name="cloud-offline-outline" size={20} color={theme.colors.warning} />
          <Text style={styles.offlineText}>Working offline</Text>
        </Surface>
      )}

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        {renderStatCard(
          'Total Projects',
          stats?.total_projects || 0,
          'folder-outline',
          theme.colors.primary
        )}
        {renderStatCard(
          'Active Workflows',
          stats?.active_workflows || 0,
          'git-network-outline',
          theme.colors.success
        )}
        {renderStatCard(
          'Completed Tasks',
          stats?.completed_tasks || 0,
          'checkmark-circle-outline',
          theme.colors.warning
        )}
        {renderStatCard(
          'AI Services',
          stats?.ai_services_used || 0,
          'brain-outline',
          theme.colors.error
        )}
      </View>

      {/* Usage Chart */}
      {chartData && (
        <Card style={styles.chartCard}>
          <Card.Content>
            <Title>Usage Trends</Title>
            <LineChart
              data={chartData}
              width={screenWidth - 60}
              height={220}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
            />
          </Card.Content>
        </Card>
      )}

      {/* Quick Actions */}
      <Card style={styles.quickActionsCard}>
        <Card.Content>
          <Title>Quick Actions</Title>
          <View style={styles.quickActions}>
            <Button
              mode="contained"
              icon="plus"
              style={styles.actionButton}
              onPress={() => {/* Navigate to new project */}}
            >
              New Project
            </Button>
            <Button
              mode="outlined"
              icon="git-network"
              style={styles.actionButton}
              onPress={() => {/* Navigate to workflow builder */}}
            >
              Build Workflow
            </Button>
          </View>
          <View style={styles.quickActions}>
            <Button
              mode="outlined"
              icon="storefront"
              style={styles.actionButton}
              onPress={() => {/* Navigate to marketplace */}}
            >
              Browse Models
            </Button>
            <Button
              mode="outlined"
              icon="people"
              style={styles.actionButton}
              onPress={() => {/* Navigate to consultants */}}
            >
              Find Experts
            </Button>
          </View>
        </Card.Content>
      </Card>

      {/* Recent Activity */}
      <Card style={styles.activitySection}>
        <Card.Content>
          <View style={styles.sectionHeader}>
            <Title>Recent Activity</Title>
            <Button
              mode="text"
              onPress={() => {/* Navigate to full activity */}}
            >
              View All
            </Button>
          </View>
          {recentActivity?.slice(0, 3).map(renderActivityItem)}
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 40,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
  },
  welcomeSubtitle: {
    color: theme.colors.onSurface,
    opacity: 0.7,
  },
  offlineIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 20,
    padding: 12,
    borderRadius: 8,
    backgroundColor: theme.colors.warningContainer,
  },
  offlineText: {
    marginLeft: 8,
    color: theme.colors.warning,
    fontWeight: '500',
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 20,
    paddingTop: 0,
  },
  statCard: {
    width: '48%',
    margin: '1%',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    elevation: 2,
  },
  statContent: {
    alignItems: 'center',
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginLeft: 8,
    color: theme.colors.onSurface,
  },
  statTitle: {
    fontSize: 12,
    color: theme.colors.onSurface,
    opacity: 0.7,
    textAlign: 'center',
  },
  chartCard: {
    margin: 20,
    marginTop: 0,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  quickActionsCard: {
    margin: 20,
    marginTop: 0,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 4,
  },
  activitySection: {
    margin: 20,
    marginTop: 0,
    marginBottom: 40,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  activityCard: {
    marginBottom: 8,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  activityInfo: {
    flex: 1,
    marginRight: 12,
  },
  activityTitle: {
    fontSize: 16,
    marginBottom: 4,
  },
  activityDescription: {
    fontSize: 14,
    opacity: 0.7,
  },
  statusChip: {
    height: 28,
  },
  timestamp: {
    fontSize: 12,
    opacity: 0.5,
    marginTop: 8,
  },
});
