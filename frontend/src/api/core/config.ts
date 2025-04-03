/**
 * API基础URL
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://127.0.0.1:8000';

// 允许的前端来源列表
export const ALLOWED_ORIGINS = [
  'https://localhost:5175',
  'https://127.0.0.1:5175'
];

/**
 * 安全配置
 */
export const SECURITY_CONFIG = {
  CSRF_HEADER: 'X-CSRFToken',
  CSRF_COOKIE: 'csrftoken',
  ENCRYPTION_KEY: import.meta.env.VITE_ENCRYPTION_KEY || 'default-encryption-key',
  SENSITIVE_FIELDS: ['password', 'token', 'secret'],
};

/**
 * 默认API请求选项
 */
export const DEFAULT_API_OPTIONS = {
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
  withCredentials: true,
  credentials: 'include',
  mode: 'cors',
  secure: true,
};

// 添加认证token处理
export function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  
  const headers: Record<string, string> = {};
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  headers['X-Request-Id'] = `req-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
  headers['X-Frontend-Origin'] = window.location.origin;
  
  return headers;
}

interface Config {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
  withCredentials: boolean;
}

// 存储当前配置的变量
let config: Config = {
  baseURL: API_BASE_URL,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 15000,
  headers: {
    ...DEFAULT_API_OPTIONS.headers,
    ...getAuthHeaders(),
  },
  withCredentials: true,
};

/**
 * 获取配置
 */
export function getConfig(): Config {
  return {
    ...config,
    headers: {
      ...DEFAULT_API_OPTIONS.headers,
      ...getAuthHeaders(),
    }
  };
}

/**
 * 设置配置
 */
export function setConfig(newConfig: Partial<Config>): void {
  config = { ...config, ...newConfig };
}

// API端点配置
export const API_ENDPOINTS = {
  // 核心系统
  core: {
    configs: '/api/v1/configs',
    health: '/api/health',
    csrf: '/api/csrf/',
  },
  
  // 用户认证API
  auth: {
    login: '/api/v1/users/auth/login/',
    token: '/api/v1/users/token/',
    refresh: '/api/v1/users/token/refresh/',
    logout: '/api/v1/users/logout/',
    csrf: '/api/auth/csrf/',
  },
  // 用户相关API
  users: {
    me: '/api/v1/users/me/',
    profile: '/api/v1/users/profile/',
    changePassword: '/api/v1/users/change-password/',
  },
  // 通知模块API
  notifications: {
    list: '/api/v1/notifications/',
    detail: (id: string) => `/api/v1/notifications/${id}/`,
    create: '/api/v1/notifications/',
    update: (id: string) => `/api/v1/notifications/${id}/`,
    delete: (id: string) => `/api/v1/notifications/${id}/`,
    markAsRead: (id: string) => `/api/v1/notifications/${id}/read/`,
    markAllAsRead: '/api/v1/notifications/mark-all-read/',
    clearRead: '/api/v1/notifications/clear-read/',
  },
  // 系统配置API
  configs: {
    list: '/api/v1/configs',
    detail: (id: string) => `/api/v1/configs/${id}`,
    update: (id: string) => `/api/v1/configs/${id}`,
  },
  // 产品管理API
  products: {
    list: '/api/v1/products/products/',
    detail: (id: string) => `/api/v1/products/products/${id}/`,
    create: '/api/v1/products/products/',
    update: (id: string) => `/api/v1/products/products/${id}/`,
    delete: (id: string) => `/api/v1/products/products/${id}/`,
    uploadExcel: '/api/v1/products/products/upload_product_excel/',
    downloadTemplate: '/api/v1/products/products/download_product_template/',
  },
};

export default {
  getConfig,
  setConfig,
  API_ENDPOINTS,
  SECURITY_CONFIG,
};
