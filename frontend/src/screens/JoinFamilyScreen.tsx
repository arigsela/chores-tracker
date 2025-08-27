import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Alert, 
  ActivityIndicator,
  TextInput,
  ScrollView
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { familyAPI, JoinFamilyResponse } from '@/api/families';

interface JoinFamilyScreenProps {
  navigation?: any;
  route?: {
    params?: {
      inviteCode?: string;
    };
  };
}

export const JoinFamilyScreen: React.FC<JoinFamilyScreenProps> = ({ navigation, route }) => {
  const { user, refreshUser } = useAuth();
  const [inviteCode, setInviteCode] = useState<string>(route?.params?.inviteCode || '');
  const [isJoining, setIsJoining] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    // If invite code is provided via route params, pre-fill it
    if (route?.params?.inviteCode) {
      setInviteCode(route.params.inviteCode);
    }
  }, [route?.params?.inviteCode]);

  const validateInviteCode = (code: string): string | null => {
    if (!code) return 'Invite code is required';
    if (code.length !== 8) return 'Invite code must be exactly 8 characters';
    if (!/^[A-Z0-9]+$/.test(code)) return 'Invite code must contain only uppercase letters and numbers';
    return null;
  };

  const handleInviteCodeChange = (text: string) => {
    // Convert to uppercase and remove invalid characters
    const cleanCode = text.toUpperCase().replace(/[^A-Z0-9]/g, '');
    setInviteCode(cleanCode);
  };

  const joinFamily = async () => {
    const validationError = validateInviteCode(inviteCode);
    if (validationError) {
      Alert.alert('Invalid Code', validationError);
      return;
    }

    try {
      setIsJoining(true);
      const response: JoinFamilyResponse = await familyAPI.joinFamily(inviteCode);
      
      if (response.success) {
        Alert.alert(
          'Success!', 
          response.message,
          [
            {
              text: 'OK',
              onPress: async () => {
                // Refresh user data to get updated family context
                if (refreshUser) {
                  await refreshUser();
                }
                // Navigate back or to family screen
                if (navigation) {
                  navigation.navigate('FamilySettings');
                } else {
                  console.log('Family joined successfully!');
                }
              }
            }
          ]
        );
      } else {
        Alert.alert('Error', response.message);
      }
    } catch (error: any) {
      console.error('Failed to join family:', error);
      let errorMessage = 'Failed to join family';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid invite code';
      } else if (error.response?.status === 404) {
        errorMessage = 'Invite code not found or expired';
      } else if (error.response?.status === 409) {
        errorMessage = error.response.data?.detail || 'You already belong to a family';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      Alert.alert('Error', errorMessage);
    } finally {
      setIsJoining(false);
    }
  };

  const goBack = () => {
    if (navigation) {
      navigation.goBack();
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Join a Family</Text>
      <Text style={styles.subtitle}>
        Enter the 8-character invite code provided by another parent to join their family.
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Family Invite Code</Text>
        <Text style={styles.description}>
          The invite code should be exactly 8 characters with uppercase letters and numbers.
        </Text>
        
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.inviteCodeInput}
            value={inviteCode}
            onChangeText={handleInviteCodeChange}
            placeholder="ABCD1234"
            placeholderTextColor="#999"
            maxLength={8}
            autoCapitalize="characters"
            autoCorrect={false}
            autoComplete="off"
          />
        </View>

        {inviteCode.length > 0 && inviteCode.length < 8 && (
          <Text style={styles.warningText}>
            Code must be exactly 8 characters ({inviteCode.length}/8)
          </Text>
        )}

        {inviteCode.length === 8 && validateInviteCode(inviteCode) && (
          <Text style={styles.errorText}>
            {validateInviteCode(inviteCode)}
          </Text>
        )}

        {inviteCode.length === 8 && !validateInviteCode(inviteCode) && (
          <Text style={styles.successText}>
            ✓ Valid invite code format
          </Text>
        )}

        <TouchableOpacity 
          style={[
            styles.primaryButton, 
            (isJoining || validateInviteCode(inviteCode)) && styles.disabledButton
          ]} 
          onPress={joinFamily}
          disabled={isJoining || !!validateInviteCode(inviteCode)}
        >
          {isJoining ? (
            <View style={styles.buttonContent}>
              <ActivityIndicator size="small" color="#fff" />
              <Text style={styles.primaryButtonText}>Joining Family...</Text>
            </View>
          ) : (
            <Text style={styles.primaryButtonText}>Join Family</Text>
          )}
        </TouchableOpacity>

        {navigation && (
          <TouchableOpacity 
            style={styles.secondaryButton} 
            onPress={goBack}
          >
            <Text style={styles.secondaryButtonText}>Cancel</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>How Family Joining Works</Text>
        <Text style={styles.infoText}>
          • The other parent creates a family and gets an invite code{'\n'}
          • They share this 8-character code with you{'\n'}
          • You enter the code to join their existing family{'\n'}
          • You'll be able to manage all children and chores together{'\n'}
          • Children will see both parents as family members
        </Text>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Important Notes</Text>
        <Text style={styles.infoText}>
          • You can only belong to one family at a time{'\n'}
          • Only parents can join families{'\n'}
          • Children automatically inherit family membership{'\n'}
          • All family members can view and manage shared chores
        </Text>
      </View>
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
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
    lineHeight: 20,
  },
  inputContainer: {
    alignItems: 'center',
    marginBottom: 15,
  },
  inviteCodeInput: {
    borderWidth: 2,
    borderColor: '#007AFF',
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 15,
    fontSize: 24,
    fontWeight: 'bold',
    letterSpacing: 3,
    textAlign: 'center',
    backgroundColor: '#f8f9fa',
    minWidth: 200,
  },
  warningText: {
    fontSize: 14,
    color: '#FF9500',
    textAlign: 'center',
    marginBottom: 15,
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    textAlign: 'center',
    marginBottom: 15,
  },
  successText: {
    fontSize: 14,
    color: '#34C759',
    textAlign: 'center',
    marginBottom: 15,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 10,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  infoCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});

export default JoinFamilyScreen;