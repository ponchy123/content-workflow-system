import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import type { UserInfo } from '@/types/common';
import { storage } from '@/utils/storage';
import { logger } from '@/utils/logger';
import { post, get } from '@/api/core/request';
import { 
  TOKEN_KEY, 
  USER_INFO_KEY, 
  LOGIN_PATH,
  USER_ROLES_KEY
} from '@/types/auth';

export function useAuth() {
  const router = useRouter();
  const token = ref<string | null>(storage.get(TOKEN_KEY));
  const userInfo = ref<UserInfo | null>(storage.get(USER_INFO_KEY));
  const loading = ref(false);

  const isAuthenticated = computed(() => !!token.value);

  const hasRole = (role: string) => {
    return userInfo.value?.roles.includes(role) || false;
  };

  const hasPermission = (permission: string) => {
    return userInfo.value?.permissions.includes(permission) || false;
  };

  const setToken = (newToken: string | null) => {
    token.value = newToken;
    if (newToken) {
      storage.set(TOKEN_KEY, newToken);
      localStorage.setItem(TOKEN_KEY, newToken);
      // 同时保存到access_token，确保API请求能正确获取token
      localStorage.setItem('access_token', newToken);
      console.log('Token已保存到localStorage的TOKEN_KEY和access_token键');
    } else {
      storage.remove(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem('access_token');
      console.log('Token已从localStorage中移除');
    }
  };

  const setUserInfo = (info: UserInfo | null) => {
    userInfo.value = info;
    if (info) {
      storage.set(USER_INFO_KEY, info);
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(info));
      // 特别保存角色信息
      localStorage.setItem(USER_ROLES_KEY, JSON.stringify(info.roles || []));
    } else {
      storage.remove(USER_INFO_KEY);
      localStorage.removeItem(USER_INFO_KEY);
      localStorage.removeItem(USER_ROLES_KEY);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      loading.value = true;
      console.log('开始登录流程，用户名:', username);
      
      let csrfToken = '';
      
      try {
        // 尝试获取CSRF令牌
        console.log('尝试获取CSRF令牌...');
        const csrfResponse = await fetch('/api/auth/csrf/', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        if (csrfResponse.ok) {
          const csrfData = await csrfResponse.json();
          console.log('CSRF响应:', csrfData);
          csrfToken = csrfData?.csrfToken || '';
        } else {
          console.warn(`获取CSRF token失败: ${csrfResponse.status}，将跳过CSRF验证直接进行登录`);
        }
      } catch (error) {
        console.warn('获取CSRF token出错，将跳过CSRF验证:', error);
      }
      
      // 准备登录请求的headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      };
      
      // 如果成功获取到CSRF token，则添加到请求头
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      console.log('尝试登录...');
      const loginResponse = await fetch('/api/v1/users/token/', {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      
      if (!loginResponse.ok) {
        const errorData = await loginResponse.json().catch(() => null);
        throw new Error(errorData?.detail || `登录失败: ${loginResponse.status}`);
      }
      
      const data = await loginResponse.json();
      console.log('登录响应:', data);
      
      // 从嵌套结构中获取tokens
      let access, refresh;
      
      if (data.data && data.data.tokens) {
        // 新格式: { status, message, data: { tokens: { access, refresh }, user } }
        access = data.data.tokens.access;
        refresh = data.data.tokens.refresh;
        
        // 同时保存用户信息
        if (data.data.user) {
          const userData = {
            ...data.data.user,
            roles: data.data.user.roles || data.data.user.groups || ['user'],
            permissions: data.data.user.permissions || data.data.user.user_permissions || []
          };
          
          setUserInfo(userData);
          console.log('从登录响应中保存用户信息:', userData);
        }
      } else {
        // 兼容旧格式: { access, refresh }
        access = data.access;
        refresh = data.refresh;
      }
      
      if (!access || !refresh) {
        throw new Error('服务器响应缺少必要的token');
      }
      
      // 保存tokens - 确保先设置token再获取用户信息
      console.log('保存tokens...');
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      storage.set('access_token', access);
      setToken(access); // 这会同时设置到TOKEN_KEY和access_token
      
      // 添加延迟，确保token已被正确保存
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 验证token是否正确保存
      const savedToken = localStorage.getItem('access_token');
      console.log('验证保存的token:', savedToken ? '已正确保存' : '保存失败');
      
      // 如果没有从登录响应中获取到用户信息，则单独获取
      if (!data.data || !data.data.user) {
        console.log('从登录响应中未获取到用户信息，尝试单独获取...');
        await refreshUserInfo();
      }
      
      return true;
    } catch (error: any) {
      console.error('登录失败:', error);
      setToken(null);
      setUserInfo(null);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const logout = async () => {
    try {
      loading.value = true;
      // 尝试调用登出API，但即使失败也继续执行登出流程
      if (token.value) {
        try {
          // 调用登出 API
          await post('/api/v1/users/auth/logout/', {});
        } catch (error) {
          console.warn('登出API调用失败，但将继续清除本地认证状态:', error);
        }
      }
    } catch (error) {
      logger.error('Logout failed:', error);
    } finally {
      // 无论API是否成功，都清除所有认证相关的数据
      setToken(null);
      setUserInfo(null);
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expire_time');
      // 清除所有可能存在的认证相关数据
      for (const key of ['user_roles', 'user_permissions', 'last_login']) {
        localStorage.removeItem(key);
      }
      loading.value = false;
      router.push(LOGIN_PATH);
    }
  };

  const refreshUserInfo = async () => {
    try {
      if (!token.value) {
        console.log('无token，跳过获取用户信息');
        return;
      }

      console.log('开始获取用户信息...');
      try {
        const response = await get('/api/v1/users/me/');
        console.log('获取用户信息成功:', response.data);
        
        // 处理用户信息
        const userData = response.data;
        
        if (userData) {
          // 确保用户对象包含必要字段
          const processedUserData = {
            ...userData,
            roles: userData.roles || userData.groups || ['user'],
            permissions: userData.permissions || userData.user_permissions || []
          };
          
          // 保存用户信息
          userInfo.value = processedUserData;
          storage.set(USER_INFO_KEY, processedUserData);
          localStorage.setItem(USER_INFO_KEY, JSON.stringify(processedUserData));
          localStorage.setItem(USER_ROLES_KEY, JSON.stringify(processedUserData.roles));
          
          console.log('用户信息保存成功:', processedUserData);
          return true;
        } else {
          throw new Error('获取用户信息失败：响应中无用户数据');
        }
      } catch (error) {
        console.error('获取用户信息API调用失败:', error);
        throw error;
      }
    } catch (error) {
      console.error('获取用户信息流程失败:', error);
      return false;
    }
  };

  const forgotPassword = async (email: string) => {
    try {
      loading.value = true;
      
      let csrfToken = '';
      
      try {
        // 尝试获取CSRF令牌
        console.log('尝试获取CSRF令牌...');
        const csrfResponse = await fetch('/api/auth/csrf/', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        if (csrfResponse.ok) {
          const csrfData = await csrfResponse.json();
          csrfToken = csrfData?.csrfToken || '';
        } else {
          console.warn(`获取CSRF token失败: ${csrfResponse.status}，将跳过CSRF验证`);
        }
      } catch (error) {
        console.warn('获取CSRF token出错，将跳过CSRF验证:', error);
      }
      
      // 准备请求headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      };
      
      // 如果成功获取到CSRF token，则添加到请求头
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      // 调用密码重置API
      const response = await fetch('/api/v1/users/password-reset/', {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `重置密码请求失败: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error('重置密码请求失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const resetPassword = async (uid: string, token: string, newPassword: string, confirmPassword: string) => {
    try {
      loading.value = true;
      
      let csrfToken = '';
      
      try {
        // 尝试获取CSRF令牌
        console.log('尝试获取CSRF令牌...');
        const csrfResponse = await fetch('/api/auth/csrf/', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        if (csrfResponse.ok) {
          const csrfData = await csrfResponse.json();
          csrfToken = csrfData?.csrfToken || '';
        } else {
          console.warn(`获取CSRF token失败: ${csrfResponse.status}，将跳过CSRF验证`);
        }
      } catch (error) {
        console.warn('获取CSRF token出错，将跳过CSRF验证:', error);
      }
      
      // 准备请求headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      };
      
      // 如果成功获取到CSRF token，则添加到请求头
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      // 调用密码重置确认API
      const response = await fetch('/api/v1/users/password-reset/confirm/', {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ 
          uid, 
          token, 
          new_password: newPassword, 
          confirm_password: confirmPassword 
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `重置密码失败: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error('重置密码失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        console.error('无刷新令牌，无法刷新token');
        throw new Error('无可用的刷新令牌');
      }

      console.log('开始刷新token...');
      const response = await fetch('/api/v1/users/token/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ refresh }),
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => '未知错误');
        console.error(`令牌刷新失败，状态码: ${response.status}，错误: ${errorText}`);
        
        // 对401错误特殊处理，表示刷新令牌已过期
        if (response.status === 401) {
          console.log('刷新令牌已过期，需要重新登录');
          // 清除所有认证状态
          setToken(null);
          setUserInfo(null);
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token_expire_time');
          router.push(LOGIN_PATH);
        }
        
        throw new Error(`令牌刷新失败: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.access) {
        console.error('令牌刷新响应中没有access字段');
        throw new Error('令牌刷新响应格式错误');
      }
      
      console.log('令牌刷新成功，正在保存新令牌');
      
      // 保存新的access token
      setToken(data.access);
      
      // 在令牌刷新后，尝试更新用户会话（非关键操作，失败不影响主流程）
      try {
        console.log('尝试更新用户会话...');
        const meResponse = await fetch('/api/v1/users/me/', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${data.access}`,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
          },
          credentials: 'include'
        });
        
        if (meResponse.ok) {
          console.log('用户会话更新成功');
        } else {
          console.warn('用户会话更新失败，但令牌刷新已成功');
        }
      } catch (sessionError) {
        console.warn('更新用户会话时出错，但不影响令牌刷新结果:', sessionError);
      }

      return data.access;
    } catch (error) {
      console.error('令牌刷新过程失败:', error);
      throw error;
    }
  };

  return {
    token,
    userInfo,
    loading,
    isAuthenticated,
    hasRole,
    hasPermission,
    login,
    logout,
    refreshUserInfo,
    setToken,
    setUserInfo,
    forgotPassword,
    resetPassword,
    refreshToken
  };
}