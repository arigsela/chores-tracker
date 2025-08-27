import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, TextInput, Alert } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { familyAPI, FamilyContext } from '@/api/families';

interface ProfileScreenProps {
  onNavigate?: (screen: string) => void;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ onNavigate }) => {
  const { user, logout } = useAuth();
  const [familyContext, setFamilyContext] = useState<FamilyContext | null>(null);
  const [loadingFamily, setLoadingFamily] = useState(true);

  useEffect(() => {
    loadFamilyContext();
  }, []);

  const loadFamilyContext = async () => {
    try {
      setLoadingFamily(true);
      const context = await familyAPI.getFamilyContext();
      setFamilyContext(context);
    } catch (error) {
      console.error('Failed to load family context:', error);
    } finally {
      setLoadingFamily(false);
    }
  };

  const [showFamilyManagement, setShowFamilyManagement] = useState(false);
  const [showJoinFamily, setShowJoinFamily] = useState(false);
  const [familyName, setFamilyName] = useState('');
  const [isCreatingFamily, setIsCreatingFamily] = useState(false);
  const [joinFamilyCode, setJoinFamilyCode] = useState('');

  const navigateToFamilySettings = () => {
    if (familyContext?.has_family && onNavigate) {
      // Navigate to FamilySettings screen for users who already have a family
      onNavigate('FamilySettings');
    } else {
      // Show inline create family form for users without a family
      setShowFamilyManagement(true);
    }
  };

  const navigateToJoinFamily = () => {
    setShowJoinFamily(true);
  };

  const createFamily = async () => {
    if (!familyName.trim()) {
      Alert.alert('Error', 'Please enter a family name');
      return;
    }

    try {
      setIsCreatingFamily(true);
      await familyAPI.createFamily(familyName.trim());
      Alert.alert('Success', 'Family created successfully!');
      await loadFamilyContext(); // Reload family data
      setShowFamilyManagement(false);
      setFamilyName('');
    } catch (error: any) {
      console.error('Failed to create family:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create family');
    } finally {
      setIsCreatingFamily(false);
    }
  };

  const joinFamily = async () => {
    if (!joinFamilyCode.trim()) {
      Alert.alert('Error', 'Please enter an invite code');
      return;
    }

    try {
      await familyAPI.joinFamily(joinFamilyCode.trim());
      Alert.alert('Success', 'Joined family successfully!');
      await loadFamilyContext(); // Reload family data
      setShowJoinFamily(false);
      setJoinFamilyCode('');
    } catch (error: any) {
      console.error('Failed to join family:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to join family');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>My Profile</Text>
      
      {/* User Information */}
      <View style={styles.profileCard}>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Username:</Text>
          <Text style={styles.value}>{user?.username}</Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>Role:</Text>
          <Text style={styles.value}>{user?.role === 'parent' ? 'Parent' : 'Child'}</Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>User ID:</Text>
          <Text style={styles.value}>{user?.id}</Text>
        </View>
        
        {user?.email && (
          <View style={styles.infoRow}>
            <Text style={styles.label}>Email:</Text>
            <Text style={styles.value}>{user.email}</Text>
          </View>
        )}
        
        {user?.full_name && (
          <View style={styles.infoRow}>
            <Text style={styles.label}>Full Name:</Text>
            <Text style={styles.value}>{user.full_name}</Text>
          </View>
        )}
      </View>

      {/* Family Information */}
      <View style={styles.profileCard}>
        <Text style={styles.cardTitle}>Family Information</Text>
        
        {loadingFamily ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#007AFF" />
            <Text style={styles.loadingText}>Loading family info...</Text>
          </View>
        ) : familyContext ? (
          <>
            <View style={styles.infoRow}>
              <Text style={styles.label}>Family Status:</Text>
              <Text style={styles.value}>
                {familyContext.has_family ? 'Member' : 'No Family'}
              </Text>
            </View>
            
            {familyContext.has_family && familyContext.family && (
              <>
                <View style={styles.infoRow}>
                  <Text style={styles.label}>Family Name:</Text>
                  <Text style={styles.value}>
                    {familyContext.family.name || 'Unnamed Family'}
                  </Text>
                </View>
                
                <View style={styles.infoRow}>
                  <Text style={styles.label}>Your Role:</Text>
                  <Text style={styles.value}>{familyContext.role}</Text>
                </View>
                
                {familyContext.can_invite && (
                  <View style={styles.infoRow}>
                    <Text style={styles.label}>Invite Code:</Text>
                    <Text style={styles.value}>{familyContext.family.invite_code}</Text>
                  </View>
                )}
              </>
            )}
            
            {/* Family Action Buttons */}
            {user?.role === 'parent' && (
              <View style={styles.familyButtons}>
                {familyContext.has_family ? (
                  <TouchableOpacity 
                    style={styles.familyButton} 
                    onPress={navigateToFamilySettings}
                  >
                    <Text style={styles.familyButtonText}>Manage Family</Text>
                  </TouchableOpacity>
                ) : (
                  <View style={styles.familyButtonsRow}>
                    <TouchableOpacity 
                      style={[styles.familyButton, styles.flexButton]} 
                      onPress={navigateToFamilySettings}
                    >
                      <Text style={styles.familyButtonText}>Create Family</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.familyButton, styles.flexButton, styles.secondaryFamilyButton]} 
                      onPress={navigateToJoinFamily}
                    >
                      <Text style={styles.secondaryFamilyButtonText}>Join Family</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            )}

            {/* Inline Family Creation Form */}
            {showFamilyManagement && !familyContext?.has_family && (
              <View style={styles.inlineForm}>
                <Text style={styles.inlineFormTitle}>Create Your Family</Text>
                <TextInput
                  style={styles.inlineInput}
                  value={familyName}
                  onChangeText={setFamilyName}
                  placeholder="Enter family name (optional)"
                  placeholderTextColor="#999"
                />
                <View style={styles.inlineButtonRow}>
                  <TouchableOpacity 
                    style={[styles.inlineButton, styles.secondaryInlineButton]} 
                    onPress={() => setShowFamilyManagement(false)}
                  >
                    <Text style={styles.secondaryInlineButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.inlineButton, styles.primaryInlineButton, isCreatingFamily && styles.disabledButton]} 
                    onPress={createFamily}
                    disabled={isCreatingFamily}
                  >
                    {isCreatingFamily ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.primaryInlineButtonText}>Create Family</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {/* Inline Join Family Form */}
            {showJoinFamily && (
              <View style={styles.inlineForm}>
                <Text style={styles.inlineFormTitle}>Join a Family</Text>
                <TextInput
                  style={styles.inlineInput}
                  value={joinFamilyCode}
                  onChangeText={setJoinFamilyCode}
                  placeholder="Enter 8-character invite code"
                  placeholderTextColor="#999"
                  maxLength={8}
                  autoCapitalize="characters"
                />
                <View style={styles.inlineButtonRow}>
                  <TouchableOpacity 
                    style={[styles.inlineButton, styles.secondaryInlineButton]} 
                    onPress={() => setShowJoinFamily(false)}
                  >
                    <Text style={styles.secondaryInlineButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.inlineButton, styles.primaryInlineButton]} 
                    onPress={joinFamily}
                  >
                    <Text style={styles.primaryInlineButtonText}>Join Family</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </>
        ) : (
          <Text style={styles.errorText}>Failed to load family information</Text>
        )}
      </View>
      
      <TouchableOpacity style={styles.logoutButton} onPress={logout}>
        <Text style={styles.logoutButtonText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  profileCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  label: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  value: {
    fontSize: 14,
    color: '#333',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 10,
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    textAlign: 'center',
    paddingVertical: 20,
  },
  familyButtons: {
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  familyButtonsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  familyButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  familyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryFamilyButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  secondaryFamilyButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  flexButton: {
    flex: 1,
  },
  logoutButton: {
    backgroundColor: '#FF3B30',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Inline form styles
  inlineForm: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 15,
    marginTop: 15,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  inlineFormTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  inlineInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    backgroundColor: '#fff',
    marginBottom: 12,
  },
  inlineButtonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  inlineButton: {
    flex: 1,
    borderRadius: 6,
    paddingVertical: 10,
    alignItems: 'center',
  },
  primaryInlineButton: {
    backgroundColor: '#007AFF',
  },
  primaryInlineButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryInlineButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  secondaryInlineButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
});