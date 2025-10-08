import { userClient } from '../client';
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  VerifyTokenResponse
} from '@/types';

export const userService = {
  login: (data: LoginRequest) =>
    userClient.post<LoginResponse>('api/auth/login/', data),

  refreshToken: (data: RefreshTokenRequest) =>
    userClient.post<RefreshTokenResponse>('api/auth/refresh/', data),

  // Verify JWT token and get current user
  verifyToken: () =>
    userClient.get<VerifyTokenResponse>('api/auth/verify-token/'),

  // Logout user and invalidate all sessions
  logout: () =>
    userClient.post('api/auth/logout/'),
};