import apiClient from '../api/client';

export const userService = {
  async getChildren() {
    try {
      const response = await apiClient.get('/users/');
      // Filter to only return children
      const children = response.data.filter(user => !user.is_parent);
      return {
        success: true,
        data: children,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch children',
      };
    }
  },

  async createChild(childData) {
    try {
      const response = await apiClient.post('/users/', {
        ...childData,
        is_parent: false,
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create child account',
      };
    }
  },
};