import { post, get } from '../core/request';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
} from '@/types/user';
import { API_ENDPOINTS } from '../core/config';

export type { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse };

// 登录
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await post<LoginResponse>(API_ENDPOINTS.auth.login, data);
  return response.data;
};

// 注册
export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await post<RegisterResponse>('/api/v1/users/users/', data);
  return response.data;
};

// 获取用户信息
export const getUserInfo = async (): Promise<User> => {
  const response = await get<User>('/api/v1/users/me/');
  return response.data;
};

// 修改密码
export const changePassword = async (userId: string, data: {
  old_password: string;
  new_password: string;
  confirm_password: string;
}): Promise<{ message: string }> => {
  const response = await post<{ message: string }>(`/api/v1/users/users/${userId}/change_password/`, data);
  return response.data;
};

// 退出登录
export const logout = async (): Promise<{ message: string }> => {
  const response = await post<{ message: string }>('/api/v1/users/logout/');
  return response.data;
};

// 记录最后一次刷新token的时间
let lastTokenRefreshTime = 0;
// 记录连续刷新失败次数
let tokenRefreshFailCount = 0;
// 最大重试次数
const MAX_REFRESH_RETRIES = 3;
// 最小重试间隔（毫秒）
const MIN_REFRESH_INTERVAL = 5000; // 5秒

// 刷新令牌
export const refreshToken = async (token: string): Promise<{ access: string }> => {
  try {
    // 检查是否需要应用退避策略
    const now = Date.now();
    const timeSinceLastRefresh = now - lastTokenRefreshTime;
    
    // 计算退避时间（基于失败次数指数增长）
    const backoffTime = Math.min(
      30000, // 最大30秒
      Math.pow(2, tokenRefreshFailCount) * 1000 // 指数退避：1秒、2秒、4秒、8秒...
    );
    
    // 如果距离上次尝试时间太短且有失败记录，则等待
    if (timeSinceLastRefresh < MIN_REFRESH_INTERVAL && tokenRefreshFailCount > 0) {
      console.log(`API模块: 令牌刷新请求过于频繁，将在${backoffTime}毫秒后重试`);
      await new Promise(resolve => setTimeout(resolve, backoffTime));
    }
    
    // 更新最后刷新时间
    lastTokenRefreshTime = Date.now();
    
    console.log('API模块: 开始刷新令牌...');
    const response = await fetch('/api/v1/users/token/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      body: JSON.stringify({ refresh: token }),
      credentials: 'include'  // 确保发送和接收cookies
    });

    if (!response.ok) {
      // 记录失败次数
      tokenRefreshFailCount++;
      
      if (tokenRefreshFailCount >= MAX_REFRESH_RETRIES) {
        console.error(`API模块: 令牌刷新失败达到最大次数(${MAX_REFRESH_RETRIES})，需要重新登录`);
        // 清除认证状态，强制重新登录
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expire_time');
        
        // 重定向到登录页
        window.location.href = '/login';
        throw new Error('Maximum refresh attempts reached');
      }
      
      const errorText = await response.text().catch(() => '未知错误');
      console.error(`API模块: 令牌刷新失败，状态码: ${response.status}，错误: ${errorText}`);
      
      // 429错误特殊处理
      if (response.status === 429) {
        let retryAfter = 30; // 默认30秒
        
        // 尝试从响应头获取重试时间
        const retryAfterHeader = response.headers.get('Retry-After');
        if (retryAfterHeader) {
          retryAfter = parseInt(retryAfterHeader, 10) || 30;
        }
        
        console.warn(`API模块: 请求频率限制，将在${retryAfter}秒后重试`);
        throw new Error(`Rate limited. Retry after ${retryAfter} seconds`);
      }
      
      throw new Error(`Token refresh failed: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.access) {
      tokenRefreshFailCount++;
      console.error('API模块: 令牌刷新响应中没有access字段');
      throw new Error('Token refresh response missing access token');
    }
    
    // 重置失败计数
    tokenRefreshFailCount = 0;
    console.log('API模块: 令牌刷新成功');

    return data;
  } catch (error) {
    console.error('API模块: 令牌刷新过程失败:', error);
    throw error;
  }
};

// 刷新令牌（别名导出，以兼容现有代码）
export const refreshTokenApi = refreshToken;
