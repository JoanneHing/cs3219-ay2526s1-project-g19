import { questionClient } from '../client';

export const questionService = {
  getTopics: async (): Promise<string[]> => {
    try {
      const response = await questionClient.get<{ topics: string[] }>('/api/topics');
      return response.data.topics ?? [];
    } catch (error) {
      console.warn('Failed to fetch topics from question service API:', error);
      return [];
    }
  },
  getDifficulties: async (): Promise<string[]> => {
    try {
      const response = await questionClient.get<{ difficulties: string[] }>('/api/difficulty');
      return response.data.difficulties ?? [];
    } catch (error) {
      console.warn('Failed to fetch difficulties from question service API:', error);
      return [];
    }
  },
};
