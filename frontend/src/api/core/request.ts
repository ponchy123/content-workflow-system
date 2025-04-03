import axios from 'axios';
import type { 
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosInstance
} from 'axios';
import { ElMessage } from 'element-plus';
import { AES, enc } from 'crypto-js';
import { ElLoading } from 'element-plus';
import { ref, computed } from 'vue';
import type { Ref, ComputedRef } from 'vue';
import { useUserStore } from '@/stores/user';
import { getConfig, API_ENDPOINTS } from './config';
import { SECURITY_CONFIG as CONFIG_SECURITY_CONFIG } from './config';
import type { SecurityConfig } from './types';
import { TOKEN_KEY, USER_INFO_KEY, USER_ROLES_KEY } from '@/types/auth';

// 用户存储类型
interface UserStore {
  token: Ref<string | null>;
  setToken: (token: string) => void;
  refreshTokenHandler: () => Promise<any>;
  logout: () => void;
  userInfo: Ref<any>;
  permissions: Ref<string[]>;
  isLoggedIn: ComputedRef<boolean>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

let _store: UserStore | null = null;

// 请求队列管理
const pendingRequests = new Map<string, AbortController>();
const requestCache = new Map<
  string,
  {
    data: any;
    timestamp: number;
    ttl: number;
  }
>();

// 请求元数据类型
interface RequestMetadata {
  startTime: number;
  duration?: number;
  retryCount?: number;
  requestId?: string;
  priority?: number;
}

// 缓存状态类型
interface CacheStatus {
  [key: string]: number;
}

// 添加防抖和节流类型定义
type DebouncedRequest = <T>(config: EnhancedAxiosRequestConfig) => Promise<T>;
type ThrottledRequest = <T>(config: EnhancedAxiosRequestConfig) => Promise<T>;

// 基础类型定义
type EnhancedAxiosError<T = any> = AxiosError<T> & {
  config?: EnhancedAxiosRequestConfig;
};

// HTTP 服务类型
interface HttpService {
  request: <T>(config: EnhancedAxiosRequestConfig) => Promise<T>;
  get: <T>(url: string, config?: Partial<EnhancedAxiosRequestConfig>) => Promise<T>;
  post: <T>(url: string, data?: any, config?: Partial<EnhancedAxiosRequestConfig>) => Promise<T>;
  put: <T>(url: string, data?: any, config?: Partial<EnhancedAxiosRequestConfig>) => Promise<T>;
  delete: <T>(url: string, config?: Partial<EnhancedAxiosRequestConfig>) => Promise<T>;
  debouncedRequest: DebouncedRequest;
  throttledRequest: ThrottledRequest;
  cancelRequest: (config: AxiosRequestConfig) => void;
  cancelAllRequests: () => void;
  clearCache: () => void;
  setCacheTTL: (ttl: number) => void;
  precacheResources: (urls: string[]) => Promise<void>;
  clearCaches: () => Promise<void>;
  getCacheStatus: () => Promise<CacheStatus | null>;
  showError: (error: EnhancedAxiosError<ErrorData>) => void;
  startLoading: (key: string, type?: string, options?: any) => void;
  endLoading: (key: string) => void;
  clearLoading: () => void;
  processData: (type: string, data: any) => Promise<any>;
  cleanupWorkers: () => void;
}

// 性能监控接口
interface PerformanceMonitor {
  startTime: number;
  start: () => void;
  end: (url: string, success: boolean) => void;
  reportPerformance: (data: PerformanceData) => Promise<void>;
  reportSlowRequest: (data: PerformanceData) => Promise<void>;
}

// 用户行为跟踪接口
interface UserBehaviorTracker {
  sessionId: string;
  lastActivityTime: number;
  trackRequest: (config: EnhancedAxiosRequestConfig) => void;
  trackResponse: (response: EnhancedAxiosResponse) => void;
  trackError: (error: any) => void;
  updateSession: () => void;
  trackEvent: (eventType: string, eventData: any) => Promise<void>;
}

// 响应元数据类型
interface ResponseMetadata {
  duration: number;
  cached: boolean;
  retries: number;
  timestamp: number;
}

// 修改请求配置类型
interface EnhancedAxiosRequestConfig extends Omit<InternalAxiosRequestConfig, 'headers'> {
  metadata?: RequestMetadata;
  retryCount?: number;
  shouldCache?: boolean;
  cacheTTL?: number;
  retryStrategy?: string;
  priority?: number;
  _retry?: boolean;
  headers: {
    'X-Loading-Type'?: string;
    'Content-Type'?: string;
    Authorization?: string;
    'X-Requested-With'?: string;
    [key: string]: string | number | boolean | undefined;
  };
  withCredentials?: boolean;
}

// 修改响应类型
interface EnhancedAxiosResponse<T = any> extends Omit<AxiosResponse<T>, 'config'> {
  config: EnhancedAxiosRequestConfig;
  metadata?: ResponseMetadata;
}

// 缓存项类型
interface CacheItem<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
}

// 性能监控数据类型
interface PerformanceData {
  url: string;
  duration: number;
  success: boolean;
  timestamp: number;
  resourceType?: string;
  errorCode?: string;
}

// 用户行为事件类型
interface TrackingEvent {
  sessionId: string;
  eventType: string;
  eventData: {
    url?: string;
    method?: string;
    status?: number;
    duration?: number;
    timestamp: number;
    [key: string]: any;
  };
}

// 错误上报数据类型
interface ErrorReport {
  type: string;
  message: string;
  stack?: string;
  timestamp: number;
  context?: {
    url?: string;
    userAgent?: string;
    [key: string]: any;
  };
}

// 安全配置类型
// interface SecurityConfig {
//   CSRF_HEADER: string;
//   CSRF_COOKIE: string;
//   ENCRYPTION_KEY: string;
//   SENSITIVE_FIELDS: string[];
// }

// 性能监控配置类型
interface PerformanceConfig {
  SLOW_REQUEST_THRESHOLD: number;
  ERROR_SAMPLE_RATE: number;
  PERFORMANCE_SAMPLE_RATE: number;
}

// 用户行为跟踪配置类型
interface TrackingConfig {
  TRACK_INTERACTIONS: boolean;
  TRACK_ERRORS: boolean;
  TRACK_PERFORMANCE: boolean;
  SESSION_TIMEOUT: number;
}

// 错误模板类型
interface ErrorTemplate {
  title: string;
  duration: number;
  type: string;
  retryable: boolean;
}

// 错误配置类型
interface ErrorConfig {
  DURATION: {
    SHORT: number;
    MEDIUM: number;
    LONG: number;
    PERMANENT: number;
  };
  TYPES: {
    NETWORK: string;
    AUTH: string;
    VALIDATION: string;
    BUSINESS: string;
    SYSTEM: string;
  };
  TEMPLATES: {
    [key: string]: ErrorTemplate;
  };
  RETRY_STRATEGIES: {
    EXPONENTIAL_BACKOFF: string;
    LINEAR_BACKOFF: string;
    FIBONACCI_BACKOFF: string;
    RANDOM_BACKOFF: string;
  };
  ERROR_ACTIONS: {
    RETRY: string;
    FALLBACK: string;
    CIRCUIT_BREAK: string;
    IGNORE: string;
    REPORT: string;
  };
  CIRCUIT_BREAKER: {
    ERROR_THRESHOLD: number;
    SUCCESS_THRESHOLD: number;
    TIMEOUT: number;
    HALF_OPEN_TIMEOUT: number;
  };
}

// 错误响应类型
interface ErrorResponse {
  title: string;
  message: string;
  type: string;
  duration: number;
  retryable: boolean;
}

// 错误数据类型
interface ErrorData {
  message?: string;
  errors?: Record<string, string[]>;
  code?: string;
}

// 添加 HTML 元素类型定义
interface HTMLProgressElement extends HTMLElement {
  style: CSSStyleDeclaration;
}

interface HTMLLoadingElement extends HTMLElement {
  style: CSSStyleDeclaration;
}

// 修改加载状态管理器类型
interface LoadingState {
  count: number;
  timer?: number;
  instance?: any;
  type?: string;
  theme?: string;
  message?: string;
}

interface LoadingOptions {
  theme?: string;
  message?: string;
  delay?: number;
}

// 修改加载状态管理器
const loadingManager = {
  loadingStates: new Map<string, LoadingState>(),

  // 开始加载
  startLoading(
    key: string,
    type: string = LOADING_CONFIG.TYPES.COMPONENT,
    options: LoadingOptions = {},
  ) {
    const state = this.loadingStates.get(key) || { count: 0 };
    state.count++;

    if (state.count === 1) {
      state.type = type;
      state.theme = options.theme || LOADING_CONFIG.THEMES.LIGHT;
      state.message = options.message || LOADING_CONFIG.MESSAGES.DEFAULT;

      // 添加延迟显示
      state.timer = window.setTimeout(() => {
        const container = this.createLoadingContainer(key, type);
        state.instance = ElLoading.service({
          target: type === LOADING_CONFIG.TYPES.FULL_SCREEN ? undefined : container,
          fullscreen: type === LOADING_CONFIG.TYPES.FULL_SCREEN,
          text: state.message,
          background:
            state.theme === LOADING_CONFIG.THEMES.DARK
              ? 'rgba(0, 0, 0, 0.7)'
              : 'rgba(255, 255, 255, 0.7)',
          customClass: `loading-${type} loading-theme-${state.theme}`,
        });

        // 添加动画元素
        const animation = this.createLoadingAnimation(type, {
          theme: state.theme,
          message: state.message,
        });
        container.appendChild(animation);
      }, options.delay || LOADING_CONFIG.DELAY);
    }

    this.loadingStates.set(key, state);
  },

  // 结束加载
  endLoading(key: string) {
    const state = this.loadingStates.get(key);
    if (!state) return;

    state.count--;
    if (state.count <= 0) {
      if (state.timer) {
        clearTimeout(state.timer);
        state.timer = undefined;
      }
      if (state.instance) {
        state.instance.close();
        state.instance = undefined;
      }
      this.loadingStates.delete(key);
      this.removeLoadingContainer(key);
    } else {
      this.loadingStates.set(key, state);
    }
  },

  // 创建加载容器
  createLoadingContainer(key: string, type: string): HTMLLoadingElement {
    let container = document.getElementById(`loading-container-${key}`) as HTMLLoadingElement;
    if (!container) {
      container = document.createElement('div') as HTMLLoadingElement;
      container.id = `loading-container-${key}`;
      container.className = `loading-container loading-container-${type}`;
      document.body.appendChild(container);
    }
    return container;
  },

  // 移除加载容器
  removeLoadingContainer(key: string) {
    const container = document.getElementById(`loading-container-${key}`);
    if (container) {
      container.remove();
    }
  },

  // 创建加载动画
  createLoadingAnimation(
    type: string,
    options: {
      theme?: string;
      message?: string;
      progress?: number;
      lines?: number;
    } = {},
  ): HTMLLoadingElement {
    const container = document.createElement('div') as HTMLLoadingElement;
    container.className = `loading-animation loading-animation-${type} loading-theme-${options.theme || LOADING_CONFIG.THEMES.LIGHT}`;

    switch (type) {
      case LOADING_CONFIG.ANIMATIONS.SPINNER:
        container.innerHTML = `
                    <div class="spinner">
                        <div class="bounce1"></div>
                        <div class="bounce2"></div>
                        <div class="bounce3"></div>
                    </div>
                    <div class="loading-text">${options.message || ''}</div>
                `;
        break;

      case LOADING_CONFIG.ANIMATIONS.PROGRESS_BAR:
        container.innerHTML = `
                    <div class="progress-bar">
                        <div class="progress" style="width: ${options.progress || 0}%"></div>
                    </div>
                    <div class="loading-text">${options.message || ''}</div>
                `;
        break;

      case LOADING_CONFIG.ANIMATIONS.SKELETON:
        container.innerHTML =
          Array(options.lines || 3)
            .fill('<div class="skeleton-line"></div>')
            .join('') + `<div class="loading-text">${options.message || ''}</div>`;
        break;

      case LOADING_CONFIG.ANIMATIONS.SHIMMER:
        container.innerHTML = `
                    <div class="shimmer-container">
                        <div class="shimmer-line"></div>
                        <div class="shimmer-animation"></div>
                    </div>
                    <div class="loading-text">${options.message || ''}</div>
                `;
        break;

      case LOADING_CONFIG.ANIMATIONS.PULSE:
        container.innerHTML = `
                    <div class="pulse-container">
                        <div class="pulse-dot"></div>
                    </div>
                    <div class="loading-text">${options.message || ''}</div>
                `;
        break;

      default:
        container.innerHTML = `
                    <div class="default-spinner"></div>
                    <div class="loading-text">${options.message || ''}</div>
                `;
    }

    return container;
  },

  // 更新加载进度
  updateProgress(key: string, progress: number) {
    const state = this.loadingStates.get(key);
    if (state?.instance) {
      const container = document.getElementById(`loading-container-${key}`);
      if (container) {
        const progressBar = container.querySelector('.progress') as HTMLProgressElement;
        if (progressBar) {
          progressBar.style.width = `${progress}%`;
        }
        const loadingText = container.querySelector('.loading-text');
        if (loadingText) {
          loadingText.textContent = `${Math.round(progress)}%`;
        }
      }
    }
  },

  // 更新加载消息
  updateMessage(key: string, message: string) {
    const state = this.loadingStates.get(key);
    if (state?.instance) {
      const container = document.getElementById(`loading-container-${key}`);
      if (container) {
        const loadingText = container.querySelector('.loading-text');
        if (loadingText) {
          loadingText.textContent = message;
        }
      }
    }
  },

  // 清理所有加载状态
  clearAll() {
    this.loadingStates.forEach(state => {
      if (state.timer) {
        clearTimeout(state.timer);
      }
      if (state.instance) {
        state.instance.close();
      }
    });
    this.loadingStates.clear();

    // 清理所有加载容器
    document.querySelectorAll('.loading-container').forEach(container => {
      container.remove();
    });
  },
};

// 生成请求标识
const generateRequestKey = (config: EnhancedAxiosRequestConfig | AxiosRequestConfig): string => {
  const { method, url, params, data } = config;
  return `${method}-${url}-${JSON.stringify(params)}-${JSON.stringify(data)}`;
};

// 缓存配置
const CACHE_CONFIG = {
  DEFAULT_TTL: 5 * 60 * 1000, // 默认缓存5分钟
  CACHE_METHODS: ['GET'],
  MAX_CACHE_SIZE: 100,
  STATIC_CACHE_NAME: 'static-v1',
  API_CACHE_NAME: 'api-v1',
  STATIC_RESOURCES: [
    '.css',
    '.js',
    '.woff',
    '.woff2',
    '.ttf',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.svg',
    '.ico',
  ],
  CACHE_STRATEGIES: {
    CACHE_FIRST: 'cache-first', // 优先使用缓存
    NETWORK_FIRST: 'network-first', // 优先使用网络
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate', // 使用缓存同时更新
  },
};

// 重试配置
const RETRY_CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
  RETRY_STATUS_CODES: [408, 500, 502, 503, 504],
  TIMEOUT: {
    DEFAULT: 10000,
    UPLOAD: 30000,
    DOWNLOAD: 30000,
    RETRY: 5000,
  },
  BACKOFF_FACTOR: 2,
  MAX_TIMEOUT: 30000,
};

// 安全配置
// const SECURITY_CONFIG: SecurityConfig = {
//   CSRF_HEADER: 'X-CSRF-TOKEN',
//   CSRF_COOKIE: 'csrf_token',
//   ENCRYPTION_KEY: import.meta.env.VITE_ENCRYPTION_KEY || 'default-key',
//   SENSITIVE_FIELDS: ['password', 'token', 'creditCard', 'idCard'],
// };

// 性能监控配置
const PERFORMANCE_CONFIG: PerformanceConfig = {
  SLOW_REQUEST_THRESHOLD: 3000, // 慢请求阈值（毫秒）
  ERROR_SAMPLE_RATE: 1.0, // 错误采样率
  PERFORMANCE_SAMPLE_RATE: 0.1, // 性能采样率
};

// 用户行为跟踪配置
const TRACKING_CONFIG: TrackingConfig = {
  TRACK_INTERACTIONS: true,
  TRACK_ERRORS: true,
  TRACK_PERFORMANCE: true,
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30分钟会话超时
};

// Token 管理配置
const TOKEN_CONFIG = {
  ROTATION_INTERVAL: 15 * 60 * 1000, // 15分钟轮换一次
  REFRESH_THRESHOLD: 5 * 60 * 1000, // 剩余5分钟时刷新
  MAX_REFRESH_RETRIES: 3, // 最大刷新重试次数
  REFRESH_RETRY_DELAY: 1000, // 刷新重试延迟
  TOKEN_TYPES: {
    ACCESS: 'access_token',
    REFRESH: 'refresh_token',
    ROTATION: 'rotation_token',
  },
};

// Token 管理器
const tokenManager = {
  refreshPromise: null as Promise<void> | null,
  refreshRetries: 0,
  rotationTimer: null as number | null,

  // 初始化 token 轮换
  initTokenRotation() {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
    }

    this.rotationTimer = window.setInterval(() => {
      this.rotateToken();
    }, TOKEN_CONFIG.ROTATION_INTERVAL);
  },

  // 轮换 token
  async rotateToken() {
    const userStore = getUserStore();
    if (!userStore.token.value) return;

    try {
      // 修改为使用正确的token刷新端点
      const response = await fetch('/api/v1/users/token/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        } as Record<string, string>,
        body: JSON.stringify({
          refresh: localStorage.getItem('refresh_token') || ''
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access) {
          userStore.setToken(data.access);
          console.log('Token已成功刷新');
        }
      } else {
        console.warn('Token刷新失败，状态码:', response.status);
        // 如果刷新失败且状态码是401，可能是refresh token已过期，需要用户重新登录
        if (response.status === 401) {
          userStore.logout();
        }
      }
    } catch (error) {
      console.error('Token刷新请求失败:', error);
    }
  },

  // 刷新 token
  async refreshToken() {
    const userStore = getUserStore();

    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = new Promise(async (resolve, reject) => {
      try {
        if (this.refreshRetries >= TOKEN_CONFIG.MAX_REFRESH_RETRIES) {
          userStore.logout();
          reject(new Error('Token refresh failed after max retries'));
          return;
        }

        const response = await userStore.refreshTokenHandler();
        this.refreshRetries = 0;
        resolve(response);
      } catch (error) {
        this.refreshRetries++;

        await new Promise(r =>
          setTimeout(r, TOKEN_CONFIG.REFRESH_RETRY_DELAY * this.refreshRetries),
        );

        reject(error);
      } finally {
        this.refreshPromise = null;
      }
    });

    return this.refreshPromise;
  },

  // 检查 token 是否需要刷新
  shouldRefreshToken() {
    const userStore = getUserStore();
    if (!userStore.token.value) return false;

    const tokenData = this.parseToken(userStore.token.value);
    if (!tokenData) return false;

    const timeUntilExpiry = tokenData.exp * 1000 - Date.now();
    return timeUntilExpiry < TOKEN_CONFIG.REFRESH_THRESHOLD;
  },

  // 解析 token
  parseToken(token: string): { exp: number } | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join(''),
      );

      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Token parsing failed:', error);
      return null;
    }
  },

  // 清理
  cleanup() {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
      this.rotationTimer = null;
    }
    this.refreshPromise = null;
    this.refreshRetries = 0;
  },
};

// 获取CSRF Token
const getCsrfToken = (): string => {
  // 首先尝试从cookie中获取
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken' || name === 'CSRF-TOKEN' || name === 'X-CSRFToken') {
      return value;
    }
  }
  
  // 如果cookie中没有，尝试从meta标签获取
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    const metaCsrf = metaTag.getAttribute('content');
    if (metaCsrf) {
      return metaCsrf;
    }
  }
  
  return '';
};

// 主动从服务器获取CSRF令牌
const fetchCsrfToken = async (): Promise<string> => {
  try {
    // 使用 core 模块的 CSRF 端点
    const response = await axios.get(API_ENDPOINTS.core.csrf, {
      withCredentials: true
    });
    
    // 从响应中获取CSRF令牌
    if (response.data && response.data.csrfToken) {
      return response.data.csrfToken;
    }
    
    // 如果响应中没有令牌，尝试从cookie中获取
    return getCsrfToken();
  } catch (error) {
    console.error('获取CSRF token失败:', error);
    return '';
  }
};

// 加密敏感数据
const encryptSensitiveData = (data: any): any => {
  if (!data) return data;

  if (typeof data === 'object') {
    const encrypted = { ...data };
    for (const key in encrypted) {
      if (CONFIG_SECURITY_CONFIG.SENSITIVE_FIELDS.includes(key)) {
        encrypted[key] = AES.encrypt(
          JSON.stringify(encrypted[key]),
          CONFIG_SECURITY_CONFIG.ENCRYPTION_KEY || 'default-encryption-key',
        ).toString();
      } else if (typeof encrypted[key] === 'object') {
        encrypted[key] = encryptSensitiveData(encrypted[key]);
      }
    }
    return encrypted;
  }
  return data;
};

// 解密敏感数据
const decryptSensitiveData = (data: any): any => {
  if (!data) return data;

  if (typeof data === 'object') {
    const decrypted = { ...data };
    for (const key in decrypted) {
      if (CONFIG_SECURITY_CONFIG.SENSITIVE_FIELDS.includes(key)) {
        try {
          const bytes = AES.decrypt(decrypted[key], CONFIG_SECURITY_CONFIG.ENCRYPTION_KEY || 'default-encryption-key');
          decrypted[key] = JSON.parse(bytes.toString(enc.Utf8));
        } catch (error) {
          console.error('解密失败:', error);
        }
      } else if (typeof decrypted[key] === 'object') {
        decrypted[key] = decryptSensitiveData(decrypted[key]);
      }
    }
    return decrypted;
  }
  return data;
};

// 清理过期缓存
const cleanExpiredCache = () => {
  const now = Date.now();
  for (const [key, value] of requestCache.entries()) {
    if (now - value.timestamp > value.ttl) {
      requestCache.delete(key);
    }
  }
};

// 定期清理缓存
setInterval(cleanExpiredCache, 60 * 1000);

// 错误类型常量
const ERROR_TYPES = {
  NETWORK: 'network',
  AUTH: 'auth',
  VALIDATION: 'validation',
  BUSINESS: 'business',
  SYSTEM: 'system',
} as const;

// 加载配置常量
const LOADING_TYPES = {
  FULL_SCREEN: 'full-screen',
  COMPONENT: 'component',
  BUTTON: 'button',
} as const;

const LOADING_ANIMATIONS = {
  SPINNER: 'spinner',
  PROGRESS_BAR: 'progress-bar',
  SKELETON: 'skeleton',
  SHIMMER: 'shimmer',
  PULSE: 'pulse',
} as const;

const LOADING_THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  CUSTOM: 'custom',
} as const;

const LOADING_POSITIONS = {
  FULL_SCREEN: 'full-screen',
  CONTAINER: 'container',
  INLINE: 'inline',
} as const;

// 错误配置
const ERROR_CONFIG: ErrorConfig = {
  DURATION: {
    SHORT: 3000,
    MEDIUM: 5000,
    LONG: 8000,
    PERMANENT: 0,
  },
  TYPES: ERROR_TYPES,
  TEMPLATES: {
    [ERROR_TYPES.NETWORK]: {
      title: '网络错误',
      duration: 5000,
      type: 'error',
      retryable: true,
    },
    [ERROR_TYPES.AUTH]: {
      title: '认证错误',
      duration: 8000,
      type: 'warning',
      retryable: false,
    },
    [ERROR_TYPES.VALIDATION]: {
      title: '验证错误',
      duration: 3000,
      type: 'warning',
      retryable: false,
    },
    [ERROR_TYPES.BUSINESS]: {
      title: '业务错误',
      duration: 5000,
      type: 'error',
      retryable: true,
    },
    [ERROR_TYPES.SYSTEM]: {
      title: '系统错误',
      duration: 8000,
      type: 'error',
      retryable: true,
    },
  },
  RETRY_STRATEGIES: {
    EXPONENTIAL_BACKOFF: 'exponential',
    LINEAR_BACKOFF: 'linear',
    FIBONACCI_BACKOFF: 'fibonacci',
    RANDOM_BACKOFF: 'random',
  },
  ERROR_ACTIONS: {
    RETRY: 'retry',
    FALLBACK: 'fallback',
    CIRCUIT_BREAK: 'break',
    IGNORE: 'ignore',
    REPORT: 'report',
  },
  CIRCUIT_BREAKER: {
    ERROR_THRESHOLD: 5,
    SUCCESS_THRESHOLD: 2,
    TIMEOUT: 60000,
    HALF_OPEN_TIMEOUT: 30000,
  },
};

// 错误处理器
const errorHandler = {
  getErrorType(error: any): string {
    if (axios.isCancel(error)) return ERROR_CONFIG.TYPES.BUSINESS;
    if (!navigator.onLine || error.message === 'Network Error') return ERROR_CONFIG.TYPES.NETWORK;
    if (error.code === 'ECONNABORTED') return ERROR_CONFIG.TYPES.NETWORK;
    if (error.response?.status === 401 || error.response?.status === 403) return ERROR_CONFIG.TYPES.AUTH;
    if (error.response?.status === 400 || error.response?.status === 422) return ERROR_CONFIG.TYPES.VALIDATION;
    if (error.response?.status >= 500) return ERROR_CONFIG.TYPES.SYSTEM;
    return ERROR_CONFIG.TYPES.BUSINESS;
  },

  formatErrorMessage(error: AxiosError<ErrorData> & { config?: EnhancedAxiosRequestConfig }): ErrorResponse {
    const type = this.getErrorType(error);
    const template = ERROR_CONFIG.TEMPLATES[type];
    let message = error.response?.data?.message || error.message || '未知错误';
    if (type === ERROR_CONFIG.TYPES.VALIDATION && error.response?.data?.errors) {
      message = Object.values(error.response.data.errors).flat().join('\n');
    }
    return { title: template.title, message, type: template.type, duration: template.duration, retryable: template.retryable };
  },

  showError(error: EnhancedAxiosError<ErrorData>) {
    const { title, message, type, duration } = this.formatErrorMessage(error);
    ElMessage({ message: `${title}: ${message}`, type: type as any, duration, showClose: true });
  },

  getRetryDelay(config: EnhancedAxiosRequestConfig, retryCount: number): number {
    const strategy = config.retryStrategy || ERROR_CONFIG.RETRY_STRATEGIES.EXPONENTIAL_BACKOFF;
    const baseDelay = RETRY_CONFIG.RETRY_DELAY;

    switch (strategy) {
      case ERROR_CONFIG.RETRY_STRATEGIES.EXPONENTIAL_BACKOFF:
        return Math.min(baseDelay * Math.pow(2, retryCount), RETRY_CONFIG.MAX_TIMEOUT);
      case ERROR_CONFIG.RETRY_STRATEGIES.LINEAR_BACKOFF:
        return Math.min(baseDelay * (retryCount + 1), RETRY_CONFIG.MAX_TIMEOUT);
      default:
        return baseDelay;
    }
  }
};

// 加载状态配置
const LOADING_CONFIG = {
  MIN_DURATION: 300,
  DELAY: 200,
  TYPES: LOADING_TYPES,
  ANIMATIONS: LOADING_ANIMATIONS,
  THEMES: LOADING_THEMES,
  POSITIONS: LOADING_POSITIONS,
  MESSAGES: {
    DEFAULT: '加载中...',
    RETRY: '正在重试...',
    TIMEOUT: '请求超时，正在重试...',
    OFFLINE: '正在使用离线数据...',
    UPLOAD: '正在上传...',
    DOWNLOAD: '正在下载...',
  },
};

// 性能监控实现
const performanceMonitor: PerformanceMonitor = {
  startTime: 0,

  start() {
    this.startTime = performance.now();
  },

  end(url: string, success: boolean) {
    const duration = performance.now() - this.startTime;

    if (Math.random() < PERFORMANCE_CONFIG.PERFORMANCE_SAMPLE_RATE) {
      this.reportPerformance({
        url,
        duration,
        success,
        timestamp: Date.now(),
        resourceType: 'xhr',
      });
    }

    if (duration > PERFORMANCE_CONFIG.SLOW_REQUEST_THRESHOLD) {
      this.reportSlowRequest({
        url,
        duration,
        success,
        timestamp: Date.now(),
        resourceType: 'xhr',
      });
    }
  },

  async reportPerformance(data: PerformanceData) {
    try {
      await fetch('/api/v1/core/monitoring/performance/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error) {
      console.error('上报性能数据失败:', error);
    }
  },

  async reportSlowRequest(data: PerformanceData) {
    try {
      // 使用最简单的方式发送请求,不需要认证和CORS处理
      fetch('/api/v1/core/monitoring/slow-request/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        mode: 'no-cors',
        credentials: 'omit'
      }).catch(err => console.error('上报慢请求失败:', err));
    } catch (error) {
      console.error('上报慢请求失败:', error);
    }
  },
};

// 修改用户行为跟踪
const userBehaviorTracker: UserBehaviorTracker = {
  sessionId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  lastActivityTime: Date.now(),

  trackRequest(config: EnhancedAxiosRequestConfig) {
    if (!TRACKING_CONFIG.TRACK_INTERACTIONS) return;

    this.updateSession();
    this.trackEvent('api_request', {
      url: config.url,
      method: config.method,
      timestamp: Date.now(),
    });
  },

  trackResponse(response: EnhancedAxiosResponse) {
    if (!TRACKING_CONFIG.TRACK_INTERACTIONS) return;

    this.updateSession();
    this.trackEvent('api_response', {
      url: response.config?.url,
      status: response.status,
      duration: response.config?.metadata?.duration,
      timestamp: Date.now(),
    });
  },

  trackError(error: any) {
    if (!TRACKING_CONFIG.TRACK_ERRORS) return;

    this.updateSession();
    this.trackEvent('error', {
      type: error.name,
      message: error.message,
      stack: error.stack,
      timestamp: Date.now(),
    });
  },

  updateSession() {
    const now = Date.now();
    if (now - this.lastActivityTime > TRACKING_CONFIG.SESSION_TIMEOUT) {
      this.sessionId = `${now}-${Math.random().toString(36).substr(2, 9)}`;
    }
    this.lastActivityTime = now;
  },

  async trackEvent(eventType: string, eventData: any) {
    // 暂时禁用跟踪功能
    return;
    
    // 原代码注释掉
    // try {
    //   await fetch('/api/v1/core/analytics/track', {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({
    //       sessionId: this.sessionId,
    //       eventType,
    //       eventData: {
    //         ...eventData,
    //         timestamp: Date.now(),
    //       },
    //     }),
    //   });
    // } catch (error) {
    //   console.warn('Failed to track event:', error);
    // }
  },
};

// 修改获取用户存储的方法
const getUserStore = (): UserStore => {
  if (!_store) {
    const store = useUserStore();
    _store = {
      token: ref(store.token) as Ref<string | null>,
      setToken: (token: string) => (store.token = token),
      refreshTokenHandler: store.refreshTokenHandler,
      logout: store.logout,
      userInfo: ref(store.userInfo) as Ref<any>,
      permissions: ref(store.permissions) as Ref<string[]>,
      isLoggedIn: computed(() => store.isLoggedIn) as ComputedRef<boolean>,
      hasPermission: (permission: string) => store.hasPermission(permission),
      hasRole: (role: string) => store.hasRole(role),
    };
  }
  return _store;
};

// 初始化 token 管理
const initializeTokenManagement = () => {
  const store = getUserStore();
  if (store.token.value) {
    tokenManager.initTokenRotation();
  }
};

// 在应用启动时调用初始化
setTimeout(initializeTokenManagement, 0);

// 清除所有认证相关的缓存数据
const clearAuthCache = () => {
  // 清除localStorage中的认证数据
  const authKeys = [
    'access_token',
    'refresh_token',
    'token_expire_time',
    'user_info',
    'user_roles',
    'token',
    'user'
  ];
  
  authKeys.forEach(key => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
  
  // 清除请求缓存
  requestCache.clear();
  
  console.log('已清除所有认证相关的缓存数据');
};

// 重定向到登录页面
const redirectToLogin = (error?: string) => {
  // 立即强制重定向到登录页面，不考虑当前路径
  console.warn('检测到401错误，强制重定向到登录页面');
  
  // 使用最直接的方式进行重定向，绕过可能的拦截
  const redirectUrl = `/auth/login?t=${Date.now()}`;
  
  try {
    // 为确保页面重定向能够执行，我们尝试多种方法
    
    // 方法1：直接替换位置
    window.location.replace(redirectUrl);
    
    // 方法2：如果方法1失败，使用href
    setTimeout(() => {
      window.location.href = redirectUrl;
    }, 100);
    
    // 方法3：如果前两种方法都失败，尝试更基础的方法
    setTimeout(() => {
      document.location.href = redirectUrl;
    }, 200);
    
    // 输出调试信息
    console.log('已触发重定向到:', redirectUrl);
  } catch (e) {
    console.error('重定向失败:', e);
    alert('登录已过期，请手动刷新页面并重新登录');
  }
};

// 创建axios实例
export const axiosInstance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});

// 修复 handleRateLimitError 函数的参数类型
const handleRateLimitError = (error: AxiosError): false | Promise<any> => {
  if (!error.response || error.response.status !== 429) return false;
  
  // 获取Retry-After头信息
  const retryAfter = error.response.headers['retry-after'] || '30';
  const waitTime = parseInt(retryAfter, 10) * 1000;
  
  console.warn(`请求被限流，将在${retryAfter}秒后重试`);
  
  // 通知用户
  ElMessage.warning({
    message: `系统检测到请求频率过高，请等待${retryAfter}秒后重试`,
    duration: 5000,
  });
  
  return new Promise((resolve) => {
    setTimeout(() => {
      // 确保错误配置存在
      if (error.config) {
        resolve(axios(error.config));
      } else {
        // 如果没有配置，无法重试
        resolve(null);
      }
    }, waitTime);
  });
};

// 添加axios请求拦截器
// 请求拦截器
axiosInstance.interceptors.request.use(
  (config) => {
    // 添加请求ID
    const requestId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    config.headers['X-Request-ID'] = requestId;
    
    // 使用类型断言解决metadata属性不存在的问题
    const enhancedConfig = config as unknown as EnhancedAxiosRequestConfig;
    
    // 记录请求开始时间
    if (enhancedConfig.metadata) {
      enhancedConfig.metadata.startTime = Date.now();
      enhancedConfig.metadata.requestId = requestId;
    } else {
      enhancedConfig.metadata = {
        startTime: Date.now(),
        requestId
      };
    }
    
    // 添加token到请求头
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && token !== 'null' && token !== 'undefined') {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`请求添加Authorization头: ${config.url}`);
    } else {
      // 如果没有有效token，检查是否访问需要认证的API
      const url = config.url || '';
      const isAuthRequired = !url.includes('/auth/') && 
                            !url.includes('/token/') &&
                            !url.includes('/public/');
      
      if (isAuthRequired) {
        console.warn(`请求缺少有效token: ${url}`);
      }
    }
    
    // 如果请求包含表单数据，不进行任何处理
    if (config.data instanceof FormData) {
      return config;
    }
    
    // 如果是JSON请求，添加CSRF token
    if (config.headers['Content-Type'] === 'application/json') {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    // 计算请求耗时
    const enhancedConfig = response.config as unknown as EnhancedAxiosRequestConfig;
    const startTime = enhancedConfig.metadata?.startTime || performance.now();
    const duration = performance.now() - startTime;

    // 如果是邮编相关的请求，且在localhost环境，确保返回模拟数据
    const url = response.config.url || '';
    const isLocalhost = typeof window !== 'undefined' && window.location.hostname.includes('localhost');
    const isPostalRequest = url.includes('/postal/') || url.includes('/postcodes/');
    
    if (isLocalhost && isPostalRequest) {
      console.log('本地环境邮编相关请求，可能使用模拟数据');
    }
    
    // 响应后处理
    if (typeof performanceMonitor !== 'undefined' && performanceMonitor.end) {
      performanceMonitor.end(response.config.url || '', true);
    }

    // 记录请求耗时
    console.log(
      `请求完成: ${response.config.method?.toUpperCase()} ${response.config.url} - ${Math.round(
        duration,
      )}ms`,
    );

    // 从队列中移除
    const requestId = `${response.config.method}-${response.config.url}`;
    if (pendingRequests && pendingRequests.delete) {
      pendingRequests.delete(requestId);
    }

    // 更新用户行为追踪
    try {
      if (typeof userBehaviorTracker !== 'undefined' && userBehaviorTracker.trackResponse) {
        // 使用as进行类型断言以避免类型错误
        userBehaviorTracker.trackResponse(response as unknown as EnhancedAxiosResponse);
      }
    } catch (e) {
      console.warn('行为追踪错误:', e);
    }

    // 结束加载状态
    const loadingKey = JSON.stringify({
      method: response.config.method,
      url: response.config.url,
    });
    if (loadingManager && loadingManager.endLoading) {
      loadingManager.endLoading(loadingKey);
    }

    return response.data;
  },
  async (error: unknown) => {
    // 首先确保我们有一个AxiosError类型
    if (!axios.isAxiosError(error)) {
      console.error('非Axios错误:', error);
      return Promise.reject({
        message: '发生未知错误',
        status: 500
      });
    }

    const axiosError = error as AxiosError<any>;
    
    // 检查是否是429错误
    if (axiosError.response?.status === 429) {
      // 获取Retry-After头信息
      const retryAfter = axiosError.response.headers['retry-after'] || '30';
      const waitTime = parseInt(retryAfter, 10) * 1000;
      
      console.warn(`请求被限流，将在${retryAfter}秒后重试`);
      
      // 通知用户
      ElMessage.warning({
        message: `系统检测到请求频率过高，请等待${retryAfter}秒后重试`,
        duration: 5000,
      });
      
      return new Promise((resolve) => {
        setTimeout(() => {
          // 确保错误配置存在
          if (axiosError.config) {
            resolve(axios(axiosError.config));
          } else {
            resolve(null);
          }
        }, waitTime);
      });
    }
    
    // 处理401错误
    if (axiosError.response?.status === 401) {
      const userStore = getUserStore();
      
      // 确保config存在
      if (!axiosError.config) {
        console.error('请求配置不存在');
        userStore.logout();
        return Promise.reject({
          message: '认证失败，请重新登录',
          status: 401
        });
      }
      
      // 避免重复刷新token导致的无限循环
      const originalRequest = axiosError.config as any;
      if (originalRequest._retry) {
        console.error('Token刷新后请求仍然失败，将清除认证状态');
        userStore.logout();
        return Promise.reject({
          message: '认证失败，请重新登录',
          status: 401
        });
      }
      
      try {
        // 标记请求已经重试过
        originalRequest._retry = true;
        
        // 尝试刷新token
        await userStore.refreshTokenHandler();
        
        // 使用新token更新请求头
        originalRequest.headers.Authorization = `Bearer ${userStore.token.value}`;
        
        // 重试请求
        return axios(originalRequest);
      } catch (refreshError) {
        console.error('尝试刷新Token失败，需要重新登录:', refreshError);
        userStore.logout();
        return Promise.reject({
          message: '登录已过期，请重新登录',
          status: 401
        });
      }
    }
    
    // 记录请求耗时
    const startTime = (axiosError.config as any)?.metadata?.startTime || performance.now();
    const duration = performance.now() - startTime;

    // 错误日志输出
    console.log(
      `请求失败: ${axiosError.config?.method?.toUpperCase() || 'UNKNOWN'} ${axiosError.config?.url || 'UNKNOWN'} - ${Math.round(duration)}ms - ${
        axiosError.response?.status || 'Unknown'
      }`,
    );
    
    // 其他错误处理逻辑...
    
    // 返回更友好的错误消息
    return Promise.reject({
      message: axiosError.response?.data?.message || '请求失败，请重试',
      status: axiosError.response?.status || 500,
      code: axiosError.response?.data?.code
    });
  }
);

// 导出基础请求方法
// export const { get, post, put, delete: del } = axiosInstance;

// 导出增强版请求方法
export const get = axiosInstance.get;
export const post = axiosInstance.post;
export const put = axiosInstance.put;

// 增强版DELETE请求实现
export const del = async <T = any>(
  url: string,
  config: Partial<EnhancedAxiosRequestConfig> = {}
): Promise<AxiosResponse<T>> => {
  try {
    console.log(`发起DELETE请求: ${url}`, config);
    const response = await axiosInstance.delete<T>(url, config);
    console.log(`DELETE请求成功: ${url}`, response);
    return response;
  } catch (error) {
    console.error(`DELETE请求失败: ${url}`, error);
    // 重新抛出错误
    throw error;
  }
};

// 导出http实例
export default axiosInstance;

/**
 * 创建带有认证和内容类型的标准请求头
 * @returns 标准请求头对象
 */
export function createAuthHeaders() {
  return {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  };
}

/**
 * 创建请求配置工厂函数
 * @param url API请求URL
 * @param data 请求数据
 * @returns 返回一个函数，用于创建不同HTTP方法的请求配置
 */
export function createRequestConfigFactory(url: string, data: any) {
  return (method: string): AxiosRequestConfig => ({
    url,
    method,
    data,
    headers: createAuthHeaders()
  });
}

/**
 * 依次尝试多种HTTP方法发送请求
 * 如果首选方法失败，会自动尝试备选方法
 * 
 * @param url API请求URL
 * @param data 请求数据
 * @param methodsToTry 要尝试的HTTP方法数组，按优先级排序
 * @returns Promise，解析为请求的响应
 */
export async function tryMultipleMethods(
  url: string, 
  data: any, 
  methodsToTry = ['post', 'patch', 'put']
): Promise<AxiosResponse> {
  // 检查是否需要将产品ID作为查询参数添加到URL中
  if (data && data.product_id && url.includes('/by_product/')) {
    // 检查URL是否已经包含查询参数
    const separator = url.includes('?') ? '&' : '?';
    url = `${url}${separator}product_id=${data.product_id}`;
    console.log('已将product_id添加到查询参数中，新URL:', url);
  }

  // 基础费率相关的API调用始终使用POST方法
  if (url.includes('base-fees/by_product')) {
    console.log('检测到基础费率API调用，强制使用POST方法');
    methodsToTry = ['post'];
  }

  console.log(`正在使用标准流程处理请求: ${url}`);
  console.log(`请求数据:`, JSON.stringify(data));

  const configFactory = createRequestConfigFactory(url, data);
  
  // 尝试第一个方法
  const firstMethod = methodsToTry[0];
  console.log(`尝试使用${firstMethod.toUpperCase()}方法发送请求到URL: ${url}`);
  
  try {
    const response = await axiosInstance(configFactory(firstMethod));
    console.log(`${firstMethod.toUpperCase()}方法请求成功，响应状态:`, response.status);
    console.log(`响应数据:`, response.data);
    return response;
  } catch (error: any) {
    console.error(`${firstMethod.toUpperCase()}方法请求失败:`, error);
    
    // 如果有更多方法可以尝试，且是由于方法不被支持而失败
    if (methodsToTry.length > 1 && error.response && (error.response.status === 405 || error.response.status === 404)) {
      // 尝试剩余的方法
      const remainingMethods = methodsToTry.slice(1);
      const nextMethod = remainingMethods[0];
      console.log(`尝试使用${nextMethod.toUpperCase()}方法重试...`);
      
      return tryMultipleMethods(url, data, remainingMethods);
    }
    
    // 如果没有更多方法可尝试或错误与HTTP方法无关，则抛出错误
    throw error;
  }
}

/**
 * 规范化和验证请求数据
 * 
 * @param data 要验证的数据
 * @param options 验证选项
 * @returns 清理和规范化后的数据
 */
export function validateAndNormalizeData(
  data: any[], 
  options: {
    requiredType?: string,
    removeFields?: string[],
    defaultValues?: Record<string, any>
  } = {}
) {
  // 检查数据类型
  if (!Array.isArray(data)) {
    throw new Error(options.requiredType 
      ? `数据格式错误，必须是${options.requiredType}类型` 
      : '数据格式错误，必须是数组类型');
  }
  
  // 规范化数据
  return data.map(item => {
    const cleanedItem = { ...item };
    
    // 应用默认值
    if (options.defaultValues) {
      Object.entries(options.defaultValues).forEach(([key, value]) => {
        if (cleanedItem[key] === undefined || cleanedItem[key] === null || cleanedItem[key] === '') {
          cleanedItem[key] = value;
        }
      });
    }
    
    // 移除指定字段
    if (options.removeFields) {
      options.removeFields.forEach(field => {
        if (field in cleanedItem) {
          delete cleanedItem[field];
        }
      });
    }
    
    return cleanedItem;
  });
}
