/// <reference types="vite/client" />

export const API_CONFIGS = {
  user: {
    baseURL: import.meta.env.VITE_USER_SERVICE_URL,
    timeout: 10000,
  },
  question: {
    baseURL: import.meta.env.VITE_QUESTION_SERVICE_URL || '/question-service-api',
    timeout: 15000,
  },
  matching: {
    // Use the proxy path from environment variable (should be /matching-service-api)
    // This avoids CORS issues during development
    baseURL: import.meta.env.VITE_MATCHING_SERVICE_URL || '/matching-service-api',
    timeout: 30000,
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