import { matchingClient } from '../client';
import type {
  MatchRequest,
  MatchResponse,
  DeleteMatchRequest,
} from '../../types';

export const matchingService = {
  // To add user to matching queue
  addToQueue: (data: MatchRequest) =>
    matchingClient.post<MatchResponse>('/api/match', data),

  // To remove user from matching queue when matched, timed out or cancelled
  removeFromQueue: (data: DeleteMatchRequest) =>
    matchingClient.delete('/api/match', { 
      params: { user_id: data.user_id } 
    }),

  getLanguages: async (): Promise<string[]> => {
    const response = await matchingClient.get<string[]>('/api/languages');
    return response.data ?? [];
  },

  // WebSocket connection helper with proxy support
  createWebSocket: (userId: string, baseUrl?: string) => {
    let wsUrl: string;
    
    // Get the configured base URL or use default proxy path
    const apiBaseUrl = baseUrl || matchingClient.defaults.baseURL || '/matching-service-api';
    
    // If using a proxy path , construct WebSocket URL using current window location
    if (apiBaseUrl.startsWith('/')) {
      // Use the current window location to build WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host; 
      wsUrl = `${protocol}//${host}${apiBaseUrl}/api/ws?user_id=${userId}`;
    } else {
      // Direct URL, convert http to ws
      const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws');
      wsUrl = `${wsBaseUrl}/api/ws?user_id=${userId}`;
    }
    
    console.log('Creating WebSocket connection to:', wsUrl);
    
    return new WebSocket(wsUrl);
  },
};