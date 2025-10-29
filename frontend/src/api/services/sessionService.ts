import { sessionClient } from '../client';

export const sessionService = {
  // End a collaboration session
  endSession: (sessionId: string) =>
    sessionClient.post(`/api/session/end?session_id=${sessionId}`),
  // Check if user has an active session
  getActiveSession: async (userId: string) => {
    try {
      const response = await sessionClient.get(`/api/session?user_id=${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching active session:', error);
      return null;
    }
  },
};
