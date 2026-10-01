import axios from 'axios';

// Configure standard axios instance
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session auth and CSRF cookies
});

// Interceptor to handle CSRF token if we were doing mutations
apiClient.interceptors.request.use((config) => {
  // Can add auth logic here if needed
  return config;
});

export default apiClient;
