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
      // The register endpoint expects form data
      const formData = new FormData();
      formData.append('username', childData.username);
      formData.append('password', childData.password);
      formData.append('is_parent', 'false');
      
      const response = await apiClient.post('/users/register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
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