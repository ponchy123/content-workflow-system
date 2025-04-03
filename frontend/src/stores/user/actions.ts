import { login, refreshToken as refreshTokenApi, getUserInfo } from '@/api/users/auth';
import type { UserInfo } from '@/types/user';
import { logger } from '@/utils/logger';
import { TOKEN_EXPIRE_TIME, DEFAULT_USER_INFO } from './constants';

// 根据实际API返回格式定义接口
interface RefreshTokenResponse {
  access: string;
  refresh?: string;
  expires_in?: number;
}

// 重命名以避免与导入的类型冲突
interface ApiLoginResponse {
  token: string;
  refresh: string;
  expires_in: number;
  user: UserInfo;
  // 添加新的API响应格式字段
  data?: {
    data?: {
      access?: string;
      refresh?: string;
      expires_in?: number;
      user?: UserInfo;
    }
  }
}

export interface State {
  userInfo: UserInfo | null;
  permissions: string[];
}

export const state = {
  userInfo: null as UserInfo | null,
  permissions: [] as string[]
};

export const actions = {
  // 刷新Token
  refreshTokenHandler: async function(this: any, providedRefreshToken?: string): Promise<string> {
    // 如果已经在刷新中，返回刷新的Promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = new Promise<string>(async (resolve, reject) => {
      try {
        // 使用提供的refreshToken或尝试从localStorage获取
        const refreshTokenToUse = providedRefreshToken || 
          localStorage.getItem('refresh_token') || 
          this.refreshToken;
          
        if (!refreshTokenToUse) {
          throw new Error('Refresh token is missing');
        }

        const response = await refreshTokenApi(refreshTokenToUse) as RefreshTokenResponse;
        
        // 根据实际API结构调整对象解构
        const access_token = response.access;
        const refresh_token = response.refresh || refreshTokenToUse;
        const expires_in = response.expires_in || TOKEN_EXPIRE_TIME;

        // 更新token
        this.token = access_token;
        this.refreshToken = refresh_token;
        this.tokenExpireTime = Date.now() + expires_in * 1000;

        logger.info('Token refreshed successfully');
        resolve(access_token);
      } catch (error) {
        logger.error('Failed to refresh token:', error);
        
        // 刷新失败，清除登录状态
        this.logout();
        reject(error);
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    });

    return this.refreshPromise;
  },

  // 用户登录
  loginAction: async function(this: any, username: string, password: string): Promise<UserInfo> {
    try {
      // 修正登录参数格式
      const credentials = { username, password };
      // 使用as unknown进行中间类型转换
      const response = await login(credentials) as unknown as ApiLoginResponse;
      
      // 记录完整响应以便调试
      logger.debug('登录响应:', response);
      
      // 根据实际API结构调整对象解构
      // 注意：检查response.data.data格式，适应新的后端API返回格式
      let access_token, refresh_token, expires_in, user;
      
      if (response.data && response.data.data) {
        // 新版API格式
        access_token = response.data.data.access || response.token;
        refresh_token = response.data.data.refresh || response.refresh;
        expires_in = response.data.data.expires_in || response.expires_in || TOKEN_EXPIRE_TIME;
        user = response.data.data.user || response.user;
      } else {
        // 旧版API格式
        access_token = response.token;
        refresh_token = response.refresh;
        expires_in = response.expires_in || TOKEN_EXPIRE_TIME;
        user = response.user;
      }
      
      if (!access_token || !refresh_token) {
        throw new Error('登录响应缺少必要的token信息');
      }
      
      // 保存登录信息
      this.token = access_token;
      this.refreshToken = refresh_token;
      this.tokenExpireTime = Date.now() + expires_in * 1000;
      this.userInfo = user;
      
      // 直接保存到localStorage，确保页面刷新时能恢复状态
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('token_expire_time', (Date.now() + expires_in * 1000).toString());
      localStorage.setItem('user_info', JSON.stringify(user));
      
      // 设置token自动刷新
      this.startTokenRefreshTimer();
      
      // 记录登录日志
      logger.info('用户登录成功:', username);
      
      return user;
    } catch (error) {
      logger.error('登录失败:', error);
      throw error;
    }
  },

  // 用户登出
  logout: async function(this: any): Promise<void> {
    try {
      // 尝试调用登出API
      const logoutUrl = '/api/v1/users/logout/';
      // 无论是否成功都继续清理本地状态
      fetch(logoutUrl, { method: 'POST' }).catch(e => console.error('登出API调用失败', e));
    } catch (error) {
      console.error('登出请求发送失败:', error);
    } finally {
      // 清除登录状态
      this.token = '';
      this.refreshToken = '';
      this.tokenExpireTime = 0;
      this.userInfo = null;
      
      // 清除localStorage中的数据
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expire_time');
      localStorage.removeItem('user_info');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('userRoles');
      
      // 清除sessionStorage中的数据
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
      
      // 清除cookies
      document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      
      // 停止token刷新定时器
      this.stopTokenRefreshTimer();
      
      // 记录登出日志
      logger.info('User logged out successfully');
    }
  },

  // 初始化用户状态
  initialize: async function(this: any): Promise<void> {
    if (this.token && this.refreshToken) {
      // 检查token是否已过期
      const now = Date.now();
      
      if (this.tokenExpireTime <= now) {
        // token已过期，尝试刷新
        try {
          await this.refreshTokenHandler();
          await this.refreshUserInfo();
        } catch (error) {
          // 刷新失败，清除登录状态
          logger.error('Failed to initialize user session:', error);
          this.logout();
          return;
        }
      } else if (this.tokenExpireTime - now < (TOKEN_EXPIRE_TIME - 300) * 1000) {
        // token即将过期，刷新用户信息
        try {
          await this.refreshUserInfo();
        } catch (error) {
          logger.error('Failed to refresh user info during initialization:', error);
        }
      }
      
      // 设置token自动刷新
      this.startTokenRefreshTimer();
      
      logger.info('User session initialized');
    } else {
      // 无token，设置默认值
      this.setDefaultUserInfo();
    }
  },

  // 刷新用户信息
  refreshUserInfo: async function(this: any): Promise<UserInfo> {
    const response = await getUserInfo();
    this.userInfo = response;
    this.permissions = response.permissions || [];
    logger.info('User info refreshed');
    return response;
  },

  // 设置默认用户信息
  setDefaultUserInfo: function(this: any): void {
    this.userInfo = DEFAULT_USER_INFO;
  },

  // 检查权限
  hasPermission: function(this: any, permission: string): boolean {
    return this.permissions.includes(permission);
  },

  // 检查角色
  hasRole: function(this: any, role: string): boolean {
    return this.userInfo?.roles?.includes(role) || false;
  }
}; 