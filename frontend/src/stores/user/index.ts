import { defineStore } from 'pinia'
import { computed, ref, onMounted } from 'vue'
import { storage } from '@/utils/storage'
import { refreshToken } from '@/api/users/auth'
import { actions, state } from './actions'
import type { State } from './actions'
import { 
  TOKEN_KEY, 
  USER_INFO_KEY, 
  USER_ROLES_KEY,
  TOKEN_REFRESH_INTERVAL,
  TOKEN_EXPIRE_TIME,
  LOGIN_PATH
} from '@/types/auth'
import { useAuth } from '@/composables/useAuth'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { post } from '@/api/core/request'

export const useUserStore = defineStore('user', () => {
  // 从localStorage检查token
  const localToken = localStorage.getItem(TOKEN_KEY);
  const token = ref<string | null>(localToken || storage.get<string>(TOKEN_KEY))
  const refreshTokenTimer = ref<NodeJS.Timeout | null>(null)
  
  // 尝试从localStorage获取用户信息
  const localUserInfo = localStorage.getItem(USER_INFO_KEY);
  let parsedUserInfo = null;
  if (localUserInfo) {
    try {
      parsedUserInfo = JSON.parse(localUserInfo);
    } catch (e) {
      console.error('解析用户信息失败:', e);
    }
  }
  
  const userInfo = ref<any>(parsedUserInfo || state.userInfo)
  const permissions = ref<string[]>(state.permissions)
  const roles = ref<string[]>(userInfo.value?.roles || [])
  const lastLogin = ref<string>(localStorage.getItem('last_login') || '')

  // 记录刷新令牌失败次数
  let refreshFailCount = 0;
  // 最大刷新失败次数
  const MAX_REFRESH_FAILURES = 3;
  // 是否正在执行刷新操作
  let isRefreshing = false;

  const isLoggedIn = computed(() => !!token.value)

  // Token refresh logic
  const startTokenRefresh = () => {
    if (refreshTokenTimer.value) {
      clearInterval(refreshTokenTimer.value)
    }

    // 计算首次刷新的延迟时间
    const tokenExpireTime = localStorage.getItem('token_expire_time');
    let initialDelay = TOKEN_REFRESH_INTERVAL;
    
    if (tokenExpireTime) {
      const expireTime = parseInt(tokenExpireTime);
      const now = Date.now();
      const timeUntilExpiry = expireTime - now;
      
      // 如果令牌即将过期（小于5分钟），立即刷新
      if (timeUntilExpiry < 5 * 60 * 1000) {
        initialDelay = 0;
      } else {
        // 在过期前5分钟刷新
        initialDelay = timeUntilExpiry - 5 * 60 * 1000;
      }
    }

    // 首次刷新
    if (initialDelay === 0) {
      refreshTokenHandler();
    } else {
      setTimeout(refreshTokenHandler, initialDelay);
    }

    // 设置定期刷新，使用更长的间隔时间以减少刷新频率
    refreshTokenTimer.value = setInterval(async () => {
      try {
        await refreshTokenHandler();
      } catch (error) {
        console.error('Token refresh failed:', error);
        
        // 增加失败计数
        refreshFailCount++;
        
        // 如果连续失败次数过多，清除刷新定时器并登出
        if (refreshFailCount >= MAX_REFRESH_FAILURES) {
          console.error(`连续${MAX_REFRESH_FAILURES}次刷新令牌失败，将停止尝试并登出`);
          clearTokenRefresh();
          logout();
        }
      }
    }, TOKEN_REFRESH_INTERVAL);
  }

  const clearTokenRefresh = () => {
    if (refreshTokenTimer.value) {
      clearInterval(refreshTokenTimer.value);
      refreshTokenTimer.value = null;
    }
    refreshFailCount = 0;
  }

  // 刷新令牌处理函数
  const refreshTokenHandler = async () => {
    // 如果已经在刷新中，不要重复执行
    if (isRefreshing) {
      console.log('已有令牌刷新操作正在进行中，跳过本次刷新');
      return null;
    }
    
    const refreshTokenValue = localStorage.getItem('refresh_token');
    if (!refreshTokenValue) {
      console.error('无刷新令牌，无法刷新token');
      return null;
    }

    try {
      isRefreshing = true;
      console.log('Store: 开始刷新token');
      
      // 使用API模块的刷新函数，它已包含退避策略和错误处理
      const result = await refreshToken(refreshTokenValue);
      
      if (result && result.access) {
        setToken(result.access);
        // 设置token过期时间
        const tokenExpiration = Date.now() + TOKEN_EXPIRE_TIME;
        localStorage.setItem('token_expire_time', tokenExpiration.toString());
        console.log('Store: Token刷新成功');
        
        // 重置失败计数
        refreshFailCount = 0;
        
        return result.access;
      } else {
        throw new Error('刷新令牌响应无效');
      }
    } catch (error: any) {
      console.error('Store: 刷新token失败:', error);
      
      // 对于429错误，延迟更长时间后再尝试
      if (error.message && error.message.includes('Rate limited')) {
        const match = error.message.match(/Retry after (\d+) seconds/);
        if (match && match[1]) {
          const retryAfter = parseInt(match[1], 10) * 1000;
          console.warn(`Store: 请求频率限制，将在${retryAfter/1000}秒后重试`);
        }
      }
      
      // 如果刷新令牌本身已过期，直接登出
      if (error.message && (
        error.message.includes('token_not_valid') || 
        error.message.includes('Maximum refresh attempts reached')
      )) {
        console.error('Store: 刷新令牌已失效，需要重新登录');
        logout();
      }
      
      return null;
    } finally {
      isRefreshing = false;
    }
  }

  // 登出函数
  const logout = async () => {
    try {
      console.log('Store: 开始登出流程');
      
      // 首先清除令牌刷新定时器
      clearTokenRefresh();
      
      // 尝试调用登出API，但即使失败也继续执行登出流程
      if (token.value) {
        try {
          // 使用带超时的请求，确保不会因为API调用而阻塞登出流程
          const logoutPromise = post('/api/v1/users/auth/logout/', {});
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('登出请求超时')), 3000)
          );
          
          await Promise.race([logoutPromise, timeoutPromise]);
          console.log('登出API调用成功');
        } catch (error) {
          console.warn('登出API调用失败，但将继续清除本地认证状态:', error);
        }
      }
      
      // 无论API是否成功，都清除所有认证相关的数据
      setToken(null);
      setUserInfo(null);
      
      // 清除所有可能存在的认证相关数据
      const keysToRemove = [
        'refresh_token', 'token_expire_time', 'user_roles', 
        'user_permissions', 'last_login', 'access_token', 
        TOKEN_KEY, USER_INFO_KEY
      ];
      
      for (const key of keysToRemove) {
        localStorage.removeItem(key);
        storage.remove(key);
      }
      
      console.log('Store: 所有认证数据已清除');
      
      // 重定向到登录页面
      router.push(LOGIN_PATH);
      
    } catch (error) {
      console.error('Store: 登出过程中出错:', error);
      // 出错时也要确保清除认证数据
      setToken(null);
      setUserInfo(null);
      
      // 清除所有认证数据
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expire_time');
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_INFO_KEY);
      
      ElMessage.error('登出过程发生错误，请刷新页面重试');
      router.push(LOGIN_PATH);
    }
  }

  const setToken = (newToken: string | null) => {
    token.value = newToken;
    if (newToken) {
      storage.set(TOKEN_KEY, newToken);
      localStorage.setItem(TOKEN_KEY, newToken);
      console.log('Store: Token设置成功', newToken.substring(0, 10) + '...');
    } else {
      storage.remove(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      console.log('Store: Token已清除');
    }
  }

  const setUserInfo = (info: any) => {
    userInfo.value = info;
    if (info) {
      storage.set(USER_INFO_KEY, info);
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(info));
      permissions.value = info.permissions || [];
      roles.value = info.roles || [];
      console.log('Store: 用户信息设置成功', info);
    } else {
      storage.remove(USER_INFO_KEY);
      localStorage.removeItem(USER_INFO_KEY);
      permissions.value = [];
      roles.value = [];
      console.log('Store: 用户信息已清除');
    }
  }

  const hasRole = (role: string) => {
    if (!roles.value.length || !role) return false;
    return roles.value.includes(role) || roles.value.includes('admin');
  }

  const hasPermission = (permission: string) => {
    if (!permissions.value.length || !permission) return false;
    return permissions.value.includes(permission) || roles.value.includes('admin');
  }

  // 初始化时确保token在localStorage和store中同步
  if (localStorage.getItem(TOKEN_KEY) && !token.value) {
    setToken(localStorage.getItem(TOKEN_KEY));
  }
  
  if (localStorage.getItem(USER_INFO_KEY) && !userInfo.value.id) {
    try {
      const storedUserInfo = JSON.parse(localStorage.getItem(USER_INFO_KEY) || '{}');
      if (storedUserInfo.id) {
        setUserInfo(storedUserInfo);
      }
    } catch (e) {
      console.error('解析存储的用户信息失败:', e);
    }
  }

  return {
    // State
    token,
    userInfo,
    permissions,
    roles,
    lastLogin,
    
    // Computed
    isLoggedIn,
    
    // Actions
    login: async (username: string, password: string) => {
      const result = await actions.loginAction(username, password);
      
      // 确保用户信息也保存到localStorage
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(result));
      
      // 设置token过期时间
      localStorage.setItem('token_expire_time', (Date.now() + TOKEN_EXPIRE_TIME).toString());
      
      // 启动令牌刷新机制
      startTokenRefresh();
      
      return result;
    },
    
    logout,
    startTokenRefresh,
    clearTokenRefresh,
    refreshTokenHandler,
    
    // 其他actions
    initialize: actions.initialize,
    refreshUserInfo: actions.refreshUserInfo,
    setDefaultUserInfo: actions.setDefaultUserInfo,
    hasPermission: hasPermission,
    hasRole: hasRole
  }
}); 