import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(), 
  removeItem: jest.fn(),
}));

describe('Auth API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Token Storage', () => {
    it('should store token in AsyncStorage', async () => {
      const token = 'test-token';
      await AsyncStorage.setItem('@chores_tracker:token', token);
      
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@chores_tracker:token',
        token
      );
    });

    it('should retrieve token from AsyncStorage', async () => {
      const token = 'test-token';
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(token);
      
      const result = await AsyncStorage.getItem('@chores_tracker:token');
      
      expect(result).toBe(token);
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('@chores_tracker:token');
    });

    it('should remove token from AsyncStorage', async () => {
      await AsyncStorage.removeItem('@chores_tracker:token');
      
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('@chores_tracker:token');
    });
  });
});