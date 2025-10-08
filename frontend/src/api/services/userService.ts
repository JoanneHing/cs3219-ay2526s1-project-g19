import { userClient } from '../clients';
import type { User, UpdateUserDto } from '@/types/user';

export const userService = {
  getProfile: () => 
    userClient.get<User>('/profile'),

  updateProfile: (data: UpdateUserDto) => 
    userClient.put<User>('/profile', data),

  getUsers: (page: number = 1, limit: number = 10) => 
    userClient.get<{ users: User[]; total: number }>('/users', {
      params: { page, limit },
    }),
};