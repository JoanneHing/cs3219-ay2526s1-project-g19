// Login Request & Response Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  phone_number: string;
  date_of_birth: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenInfo {
  token: string;
  expires_at: string;
}

export interface Tokens {
  access_token: TokenInfo;
  refresh_token: TokenInfo;
}

export interface SessionProfile {
  profile_id: string;
  session_key: string;
  ip_address: string;
  user_agent: string;
  login_at: string;
  last_activity_at: string;
  is_active: boolean;
}

export interface LoginResponse {
  user: User;
  tokens: Tokens;
  session_profile: SessionProfile;
}

// Refresh Token Types
export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  tokens: Tokens;
}
