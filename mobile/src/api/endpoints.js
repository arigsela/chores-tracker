// API endpoint constants
export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: '/users/login',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
  },
  
  // User endpoints
  USERS: {
    ME: '/users/me',
    LIST: '/users/',
    CREATE: '/users/',
    UPDATE: (id) => `/users/${id}`,
    DELETE: (id) => `/users/${id}`,
  },
  
  // Chore endpoints
  CHORES: {
    LIST: '/chores/',
    CREATE: '/chores/',
    GET: (id) => `/chores/${id}`,
    UPDATE: (id) => `/chores/${id}`,
    DELETE: (id) => `/chores/${id}`,
    COMPLETE: (id) => `/chores/${id}/complete`,
    APPROVE: (id) => `/chores/${id}/approve`,
    DISABLE: (id) => `/chores/${id}/disable`,
  },
};
