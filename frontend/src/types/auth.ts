/**
 * 认证相关的常量配置
 * 统一管理认证相关的键名和配置，避免在项目中出现多种不同的键名
 */

/** 令牌存储的键名 */
export const TOKEN_KEY = 'access_token';

/** 用户信息存储的键名 */
export const USER_INFO_KEY = 'user_info';

/** 令牌刷新间隔（毫秒） */
export const TOKEN_REFRESH_INTERVAL = 25 * 60 * 1000; // 25分钟

/** 令牌过期时间（毫秒） */
export const TOKEN_EXPIRE_TIME = 30 * 60 * 1000; // 30分钟

/** 用户角色存储的键名 */
export const USER_ROLES_KEY = 'user_roles';

/** 记住登录的用户名键名 */
export const REMEMBERED_USERNAME_KEY = 'remembered_username';

/** 登录页的路径 */
export const LOGIN_PATH = '/auth/login';

/** 默认的重定向路径 */
export const DEFAULT_REDIRECT_PATH = '/dashboard';

/** 管理员默认的重定向路径 */
export const ADMIN_REDIRECT_PATH = '/admin/dashboard';

/** 白名单路径列表（不需要认证的路径） */
export const WHITE_LIST_PATHS = [
  '/auth/login',
  '/auth/register',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/404',
  '/403',
  '/500'
];

// 用户信息类型定义
export interface UserInfo {
  id: number;
  username: string;
  email?: string;
  roles: string[];
  permissions: string[];
  [key: string]: any;
}

// 登录请求类型
export interface LoginRequest {
  username: string;
  password: string;
}

// 登录响应类型
export interface LoginResponse {
  access: string;
  refresh: string;
  user?: UserInfo;
}

// 注册请求类型
export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
}

// 注册响应类型
export interface RegisterResponse {
  id: number;
  username: string;
  email?: string;
} 