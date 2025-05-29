/**
 * Utility function to get the WebSocket URL based on the current environment
 * Handles both client-side and server-side execution
 */

export const getWebSocketUrl = (): string => {
  const isServer = typeof window === 'undefined';
  const isProduction = process.env.NODE_ENV === 'production';
  
  // In production, use NEXT_PUBLIC_API_URL or default to production URL
  if (isProduction) {
    return (process.env.NEXT_PUBLIC_API_URL || 'https://api.consumerreports.org').replace(/^http/, 'ws') + '/ws';
  }
  
  // In development, use different URLs for server and client
  if (isServer) {
    return (process.env.INTERNAL_API_URL || 'ws://web:8000') + '/ws';
  } else {
    return (process.env.NEXT_PUBLIC_API_URL || 'ws://localhost:8000') + '/ws';
  }
};
