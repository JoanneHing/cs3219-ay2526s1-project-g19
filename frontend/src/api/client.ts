import axios from 'axios';
import { API_CONFIGS, COMMON_HEADERS } from './config';
import { setupInterceptors } from './interceptors';

// Create separate clients for each service
export const userClient = axios.create({
  ...API_CONFIGS.user,
  headers: COMMON_HEADERS,
});

// export const authClient = axios.create({
//   ...API_CONFIGS.auth,
//   headers: COMMON_HEADERS,
// });

// Setup interceptors for all clients
setupInterceptors(userClient);
// setupInterceptors(authClient);