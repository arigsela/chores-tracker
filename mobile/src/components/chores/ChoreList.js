import React from 'react';
import {
  FlatList,
  RefreshControl,
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import ChoreCard from './ChoreCard';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ChoreList = ({
  chores,
  isLoading,
  isRefreshing,
  onRefresh,
  onChorePress,
  showActions = false,
  onComplete,
  onApprove,
  emptyMessage = 'No chores found',
  ListHeaderComponent,
}) => {
  const renderEmpty = () => {
    if (isLoading && !isRefreshing) {
      return (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      );
    }

    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>{emptyMessage}</Text>
      </View>
    );
  };

  const renderItem = ({ item }) => (
    <ChoreCard
      chore={item}
      onPress={() => onChorePress && onChorePress(item)}
      showActions={showActions}
      onComplete={onComplete}
      onApprove={onApprove}
    />
  );

  return (
    <FlatList
      data={chores}
      renderItem={renderItem}
      keyExtractor={(item) => item.id.toString()}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={onRefresh}
          colors={[colors.primary]}
          tintColor={colors.primary}
        />
      }
      ListEmptyComponent={renderEmpty}
      ListHeaderComponent={ListHeaderComponent}
      contentContainerStyle={chores.length === 0 ? styles.emptyList : styles.list}
      showsVerticalScrollIndicator={false}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    paddingVertical: 8,
  },
  emptyList: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

export default ChoreList;