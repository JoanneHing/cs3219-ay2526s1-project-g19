import { sessionClient } from '../client';

export const sessionService = {
  // End a collaboration session
  endSession: (sessionId: string) =>
    sessionClient.post(`/api/session/end?session_id=${sessionId}`),
};
