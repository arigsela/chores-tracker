import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Alert, 
  ActivityIndicator,
  TextInput,
  ScrollView,
  Share,
  Clipboard
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { familyAPI, FamilyContext, FamilyMembers, InviteCodeResponse } from '@/api/families';

interface FamilySettingsScreenProps {
  onNavigate?: (screen: string) => void;
}

export const FamilySettingsScreen: React.FC<FamilySettingsScreenProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [familyContext, setFamilyContext] = useState<FamilyContext | null>(null);
  const [familyMembers, setFamilyMembers] = useState<FamilyMembers | null>(null);
  const [inviteCode, setInviteCode] = useState<string>('');
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [familyName, setFamilyName] = useState<string>('');
  const [isCreatingFamily, setIsCreatingFamily] = useState(false);

  useEffect(() => {
    loadFamilyData();
  }, []);

  const loadFamilyData = async () => {
    try {
      setLoading(true);
      const context = await familyAPI.getFamilyContext();
      setFamilyContext(context);
      
      if (context.has_family && context.family) {
        setInviteCode(context.family.invite_code);
        const members = await familyAPI.getFamilyMembers();
        setFamilyMembers(members);
      }
    } catch (error) {
      console.error('Failed to load family data:', error);
      Alert.alert('Error', 'Failed to load family information');
    } finally {
      setLoading(false);
    }
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
      await loadFamilyData(); // Reload data
    } catch (error: any) {
      console.error('Failed to create family:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create family');
    } finally {
      setIsCreatingFamily(false);
    }
  };

  const generateInviteCode = async () => {
    try {
      setIsGeneratingCode(true);
      const response: InviteCodeResponse = await familyAPI.generateInviteCode();
      setInviteCode(response.invite_code);
      Alert.alert('Success', 'New invite code generated!');
    } catch (error: any) {
      console.error('Failed to generate invite code:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to generate invite code');
    } finally {
      setIsGeneratingCode(false);
    }
  };

  const shareInviteCode = async () => {
    if (!inviteCode) return;

    const shareData = {
      title: 'Join Our Family in Chores Tracker',
      message: `Use this code to join our family: ${inviteCode}`
    };

    try {
      if (Share?.share) {
        await Share.share(shareData);
      } else {
        // Fallback for platforms that don't support Share API
        await Clipboard.setString(inviteCode);
        Alert.alert('Copied!', 'Invite code copied to clipboard');
      }
    } catch (error) {
      console.error('Failed to share invite code:', error);
      // Fallback to clipboard
      try {
        await Clipboard.setString(inviteCode);
        Alert.alert('Copied!', 'Invite code copied to clipboard');
      } catch (clipboardError) {
        Alert.alert('Error', 'Failed to copy invite code');
      }
    }
  };

  const copyInviteCode = async () => {
    if (!inviteCode) return;
    
    try {
      await Clipboard.setString(inviteCode);
      Alert.alert('Copied!', 'Invite code copied to clipboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to copy invite code');
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading family settings...</Text>
      </View>
    );
  }

  // Show create family form if user has no family
  if (!familyContext?.has_family) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => onNavigate?.('Profile')}
          >
            <Text style={styles.backButtonText}>← Back to Profile</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Create Your Family</Text>
        </View>
        <Text style={styles.subtitle}>
          Create a family to invite other parents and manage children together.
        </Text>

        <View style={styles.createFamilyCard}>
          <Text style={styles.cardTitle}>Family Name (Optional)</Text>
          <TextInput
            style={styles.textInput}
            value={familyName}
            onChangeText={setFamilyName}
            placeholder="Enter family name (e.g., The Smith Family)"
            placeholderTextColor="#999"
          />
          
          <TouchableOpacity 
            style={[styles.primaryButton, isCreatingFamily && styles.disabledButton]} 
            onPress={createFamily}
            disabled={isCreatingFamily}
          >
            {isCreatingFamily ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Create Family</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  // Show family management if user has a family
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => onNavigate?.('Profile')}
        >
          <Text style={styles.backButtonText}>← Back to Profile</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Family Settings</Text>
      </View>
      
      {/* Family Information */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Family Information</Text>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Family Name:</Text>
          <Text style={styles.value}>
            {familyContext.family?.name || 'Unnamed Family'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Total Members:</Text>
          <Text style={styles.value}>{familyMembers?.total_members || 0}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Parents:</Text>
          <Text style={styles.value}>{familyMembers?.parents.length || 0}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Children:</Text>
          <Text style={styles.value}>{familyMembers?.children.length || 0}</Text>
        </View>
      </View>

      {/* Invite Code Management */}
      {familyContext.can_invite && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Invite Other Parents</Text>
          <Text style={styles.description}>
            Share this code with another parent to invite them to your family.
          </Text>
          
          {inviteCode && (
            <View style={styles.inviteCodeContainer}>
              <Text style={styles.inviteCodeLabel}>Current Invite Code:</Text>
              <View style={styles.inviteCodeBox}>
                <Text style={styles.inviteCode}>{inviteCode}</Text>
              </View>
            </View>
          )}

          <View style={styles.buttonRow}>
            <TouchableOpacity 
              style={[styles.secondaryButton, styles.flexButton]} 
              onPress={generateInviteCode}
              disabled={isGeneratingCode}
            >
              {isGeneratingCode ? (
                <ActivityIndicator size="small" color="#007AFF" />
              ) : (
                <Text style={styles.secondaryButtonText}>Generate New Code</Text>
              )}
            </TouchableOpacity>
            
            {inviteCode && (
              <TouchableOpacity 
                style={[styles.primaryButton, styles.flexButton]} 
                onPress={shareInviteCode}
              >
                <Text style={styles.primaryButtonText}>Share Code</Text>
              </TouchableOpacity>
            )}
          </View>

          {inviteCode && (
            <TouchableOpacity 
              style={styles.copyButton} 
              onPress={copyInviteCode}
            >
              <Text style={styles.copyButtonText}>Copy to Clipboard</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Family Members */}
      {familyMembers && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Family Members</Text>
          
          {/* Parents */}
          {familyMembers.parents.length > 0 && (
            <>
              <Text style={styles.sectionLabel}>Parents</Text>
              {familyMembers.parents.map((parent) => (
                <View key={parent.id} style={styles.memberItem}>
                  <Text style={styles.memberName}>{parent.username}</Text>
                  <Text style={styles.memberRole}>Parent</Text>
                </View>
              ))}
            </>
          )}

          {/* Children */}
          {familyMembers.children.length > 0 && (
            <>
              <Text style={styles.sectionLabel}>Children</Text>
              {familyMembers.children.map((child) => (
                <View key={child.id} style={styles.memberItem}>
                  <Text style={styles.memberName}>{child.username}</Text>
                  <Text style={styles.memberRole}>Child</Text>
                </View>
              ))}
            </>
          )}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
    lineHeight: 22,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  createFamilyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
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
    paddingVertical: 8,
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
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
    lineHeight: 20,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 20,
    backgroundColor: '#fff',
  },
  inviteCodeContainer: {
    marginBottom: 15,
  },
  inviteCodeLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  inviteCodeBox: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginBottom: 15,
  },
  inviteCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    letterSpacing: 2,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
  },
  flexButton: {
    flex: 1,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  copyButton: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  copyButtonText: {
    color: '#6c757d',
    fontSize: 14,
    fontWeight: '500',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 10,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 15,
    marginBottom: 10,
  },
  memberItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  memberName: {
    fontSize: 16,
    color: '#333',
  },
  memberRole: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  header: {
    marginBottom: 20,
  },
  backButton: {
    marginBottom: 10,
  },
  backButtonText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
});

export default FamilySettingsScreen;