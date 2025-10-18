/// <reference types="vite/client" />

const ensureTrailingSlash = (rawUrl?: string): string => {
  if (!rawUrl || rawUrl.trim() === '') {
    return '';
  }
  return rawUrl.endsWith('/') ? rawUrl : `${rawUrl}/`;
};

const USER_SERVICE_BASE = ensureTrailingSlash(import.meta.env.VITE_USER_SERVICE_URL) || '/user-service-api/';

export const API_CONFIGS = {
  user: {
    baseURL: USER_SERVICE_BASE,
    timeout: 10000,
  },
  // order: {
  //   baseURL: ensureTrailingSlash(import.meta.env.VITE_ORDER_SERVICE_URL) || 'http://localhost:8002/',
  //   timeout: 10000,
  // },
  // product: {
  //   baseURL: ensureTrailingSlash(import.meta.env.VITE_PRODUCT_SERVICE_URL) || 'http://localhost:8003/',
  //   timeout: 10000,
  // },
  // auth: {
  //   baseURL: ensureTrailingSlash(import.meta.env.VITE_AUTH_SERVICE_URL) || 'http://localhost:8004/',
  //   timeout: 10000,
  // },
};

export const COMMON_HEADERS = {
  'Content-Type': 'application/json',
};
