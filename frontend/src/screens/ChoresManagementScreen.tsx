import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Switch,
} from 'react-native';
import { Chore, choreAPI } from '../api/chores';
import ChoreFormScreen from './ChoreFormScreen';

const ChoresManagementScreen: React.FC = () => {
  const [chores, setChores] = useState<Chore[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingChore, setEditingChore] = useState<Chore | undefined>();
  const [showDisabled, setShowDisabled] = useState(false);

  useEffect(() => {
    fetchChores();
  }, []);

  const fetchChores = async () => {
    try {
      // Get all chores for the parent
      const allChores = await choreAPI.getMyChores();
      setChores(allChores);
    } catch (error) {
      console.error('Failed to fetch chores:', error);
      Alert.alert('Error', 'Failed to load chores');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchChores();
  };

  const handleCreateNew = () => {
    setEditingChore(undefined);
    setShowForm(true);
  };

  const handleEdit = (chore: Chore) => {
    setEditingChore(chore);
    setShowForm(true);
  };

  const handleSave = (savedChore: Chore) => {
    setShowForm(false);
    setEditingChore(undefined);
    fetchChores(); // Refresh the list
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingChore(undefined);
  };

  const handleToggleDisable = async (chore: Chore) => {
    const isDisabled = chore.is_disabled || false;
    const action = isDisabled ? 'enable' : 'disable';
    
    Alert.alert(
      `${isDisabled ? 'Enable' : 'Disable'} Chore`,
      `Are you sure you want to ${action} "${chore.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: isDisabled ? 'Enable' : 'Disable',
          style: isDisabled ? 'default' : 'destructive',
          onPress: async () => {
            try {
              if (isDisabled) {
                await choreAPI.enableChore(chore.id);
                Alert.alert('Success', 'Chore enabled successfully');
              } else {
                await choreAPI.disableChore(chore.id);
                Alert.alert('Success', 'Chore disabled successfully');
              }
              fetchChores();
            } catch (error) {
              console.error(`Failed to ${action} chore:`, error);
              Alert.alert('Error', `Failed to ${action} chore`);
            }
          },
        },
      ]
    );
  };

  const handleDelete = (chore: Chore) => {
    Alert.alert(
      'Delete Chore',
      `Are you sure you want to permanently delete "${chore.title}"? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await choreAPI.deleteChore(chore.id);
              Alert.alert('Success', 'Chore deleted successfully');
              fetchChores();
            } catch (error) {
              console.error('Failed to delete chore:', error);
              Alert.alert('Error', 'Failed to delete chore');
            }
          },
        },
      ]
    );
  };

  const renderChoreCard = (chore: Chore) => {
    const isDisabled = chore.is_disabled || false;
    const isCompleted = chore.is_completed || chore.completed_at || chore.completion_date;
    const isPending = isCompleted && !(chore.is_approved || chore.approved_at);
    
    let statusText = 'Active';
    let statusColor = '#4caf50';
    
    if (isDisabled) {
      statusText = 'Disabled';
      statusColor = '#9e9e9e';
    } else if (isPending) {
      statusText = 'Pending Approval';
      statusColor = '#ff9800';
    } else if (isCompleted) {
      statusText = 'Completed';
      statusColor = '#2196f3';
    }

    const rewardText = chore.is_range_reward 
      ? `$${chore.min_reward?.toFixed(2)} - $${chore.max_reward?.toFixed(2)}`
      : `$${chore.reward?.toFixed(2) || '0.00'}`;

    return (
      <View key={chore.id} style={[styles.choreCard, isDisabled && styles.disabledCard]}>
        <View style={styles.choreHeader}>
          <View style={styles.choreTitleContainer}>
            <Text style={[styles.choreTitle, isDisabled && styles.disabledText]}>
              {chore.title}
            </Text>
            <View style={[styles.statusBadge, { backgroundColor: statusColor }]}>
              <Text style={styles.statusText}>{statusText}</Text>
            </View>
          </View>
        </View>

        {chore.description && (
          <Text style={[styles.choreDescription, isDisabled && styles.disabledText]}>
            {chore.description}
          </Text>
        )}

        <View style={styles.choreDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Reward:</Text>
            <Text style={[styles.detailValue, isDisabled && styles.disabledText]}>
              {rewardText}
            </Text>
          </View>
          
          {chore.is_recurring && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Frequency:</Text>
              <Text style={[styles.detailValue, isDisabled && styles.disabledText]}>
                Every {chore.cooldown_days} day(s)
              </Text>
            </View>
          )}

          {(chore.assignee_id || chore.assigned_to_id) && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Assigned to:</Text>
              <Text style={[styles.detailValue, isDisabled && styles.disabledText]}>
                Child #{chore.assignee_id || chore.assigned_to_id}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.choreActions}>
          <TouchableOpacity
            style={[styles.actionButton, styles.editButton]}
            onPress={() => handleEdit(chore)}
            disabled={isPending}
          >
            <Text style={styles.actionButtonText}>Edit</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.actionButton,
              isDisabled ? styles.enableButton : styles.disableButton,
            ]}
            onPress={() => handleToggleDisable(chore)}
          >
            <Text style={styles.actionButtonText}>
              {isDisabled ? 'Enable' : 'Disable'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => handleDelete(chore)}
            disabled={isPending}
          >
            <Text style={styles.deleteButtonText}>Delete</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (showForm) {
    return (
      <ChoreFormScreen
        chore={editingChore}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  const filteredChores = showDisabled 
    ? chores 
    : chores.filter(c => !c.is_disabled);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Manage Chores</Text>
        <TouchableOpacity style={styles.createButton} onPress={handleCreateNew}>
          <Text style={styles.createButtonText}>+ New Chore</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.filterBar}>
        <Text style={styles.filterLabel}>Show disabled chores</Text>
        <Switch
          value={showDisabled}
          onValueChange={setShowDisabled}
          trackColor={{ false: '#ccc', true: '#2196f3' }}
          thumbColor={showDisabled ? '#1976d2' : '#f4f3f4'}
        />
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {filteredChores.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>
              {showDisabled ? 'No chores found' : 'No active chores'}
            </Text>
            <Text style={styles.emptySubtext}>
              Tap "New Chore" to create your first chore
            </Text>
          </View>
        ) : (
          <View style={styles.choresList}>
            {filteredChores.map(renderChoreCard)}
          </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  createButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  createButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  filterBar: {
    backgroundColor: '#fff',
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  filterLabel: {
    fontSize: 16,
    color: '#333',
  },
  scrollView: {
    flex: 1,
  },
  choresList: {
    padding: 16,
    gap: 12,
  },
  choreCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  disabledCard: {
    opacity: 0.7,
    backgroundColor: '#f5f5f5',
  },
  choreHeader: {
    marginBottom: 8,
  },
  choreTitleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  choreTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 8,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  choreDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  choreDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 14,
    color: '#999',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  disabledText: {
    color: '#999',
  },
  choreActions: {
    flexDirection: 'row',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  editButton: {
    backgroundColor: '#2196f3',
  },
  disableButton: {
    backgroundColor: '#ff9800',
  },
  enableButton: {
    backgroundColor: '#4caf50',
  },
  deleteButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#f44336',
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  deleteButtonText: {
    color: '#f44336',
    fontWeight: '600',
    fontSize: 14,
  },
  emptyState: {
    padding: 48,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});

export default ChoresManagementScreen;