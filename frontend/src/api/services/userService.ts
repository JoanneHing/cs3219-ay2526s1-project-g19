import { userClient } from '../client';
import type { LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse } from '../type';

export const userService = {
  login: (data: LoginRequest) =>
    userClient.post<LoginResponse>('api/auth/login/', data),

  refreshToken: (data: RefreshTokenRequest) =>
    userClient.post<RefreshTokenResponse>('api/auth/refresh/', data),
};