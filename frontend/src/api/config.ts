/// <reference types="vite/client" />

export const API_CONFIGS = {
  user: {
    baseURL: import.meta.env.VITE_USER_SERVICE_URL,
    timeout: 10000,
  },
  // order: {
  //   baseURL: import.meta.env.VITE_ORDER_SERVICE_URL || 'http://localhost:8002/',
  //   timeout: 10000,
  // },
  // product: {
  //   baseURL: import.meta.env.VITE_PRODUCT_SERVICE_URL || 'http://localhost:8003/',
  //   timeout: 10000,
  // },
  // auth: {
  //   baseURL: import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8004/',
  //   timeout: 10000,
  // },
};

export const COMMON_HEADERS = {
  'Content-Type': 'application/json',
};