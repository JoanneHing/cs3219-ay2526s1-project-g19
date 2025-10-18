export interface MatchingSelections {
  topics: string[];
  difficulty: string[];
  primary_lang: string | null;
  secondary_lang: string[];
  proficiency: number;
}

export interface MatchRequest {
  user_id: string;
  criteria: MatchingSelections;
}

export interface MatchResponse {
  status: string;
  queue_id: string;
  timeout: number;
}

export interface MatchedSelections {
  topic: string;
  difficulty: string;
  language: string;
}

export interface WebSocketMessage {
  status: 'success' | 'timeout' | 'relax';
  matched_user_id: string | null;
  criteria: MatchedSelections | null;
  message?: string; // Error messages
}

export interface DeleteMatchRequest {
  user_id: string;
}