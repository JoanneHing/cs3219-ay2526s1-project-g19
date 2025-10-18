import { questionClient } from '../client';

interface TopicsResponse {
  topics: string[];
}

interface DifficultiesResponse {
  difficulties: string[];
}

export const questionService = {
  getTopics: async (): Promise<string[]> => {
    const response = await questionClient.get<TopicsResponse>('/api/topics');
    return response.data.topics ?? [];
  },
  getDifficulties: async (): Promise<string[]> => {
    const response = await questionClient.get<DifficultiesResponse>('/api/difficulty');
    return response.data.difficulties ?? [];
  },
};
