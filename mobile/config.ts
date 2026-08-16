import { Platform } from 'react-native';

/**
 * Global configuration for the mobile client.
 * Reads API URL from EXPO_PUBLIC_API_URL if defined, otherwise falls back to localhost.
 */
export const API_URL = 
  process.env.EXPO_PUBLIC_API_URL || 
  (Platform.OS === 'web' ? 'http://localhost:8000' : 'http://localhost:8000');
