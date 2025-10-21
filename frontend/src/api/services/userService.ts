import { userClient } from '../client';
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  VerifyTokenResponse,
  RegisterRequest,
  RegisterResponse,
  EmailSSORequest,
  EmailSSOResponse,
  EmailSSOVerifyRequest,
  EmailSSOVerifyResponse
} from '@/types';

export const userService = {
  register: (data: RegisterRequest) =>
    userClient.post<RegisterResponse>('api/auth/register/', data),

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

  // Email SSO - Request magic link
  requestEmailSSO: (data: EmailSSORequest) =>
    userClient.post<EmailSSOResponse>('api/auth/email-sso/', data),

  // Email SSO - Verify token and login
  verifyEmailSSO: (data: EmailSSOVerifyRequest) =>
    userClient.post<EmailSSOVerifyResponse>('api/auth/email-sso/verify/', data),
};