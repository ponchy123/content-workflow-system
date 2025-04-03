<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2 class="header-title">欢迎回来</h2>
          <p class="header-subtitle">请登录您的账号</p>
        </div>
      </template>
      
      <!-- 添加错误提示 -->
      <el-alert
        v-if="errorMessage"
        type="error"
        :title="errorMessage"
        :closable="true"
        show-icon
        style="margin-bottom: 20px;"
      />
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <div class="form-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-link type="primary" :underline="false" @click="goToForgotPassword">忘记密码？</el-link>
        </div>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
        
        <div class="register-link">
          还没有账号？
          <el-link type="primary" @click="goToRegister">立即注册</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import type { FormInstance } from 'element-plus';
import { useAuth } from '@/composables/useAuth';
import { useUserStore } from '@/stores/user';
import { storage } from '@/utils/storage';
import { useRoute } from 'vue-router';

const loginFormRef = ref<FormInstance>();
const loginForm = ref({
  username: '',
  password: '',
});
const loading = ref(false);
const rememberMe = ref(false);
const router = useRouter();
const { login } = useAuth();
const userStore = useUserStore();
const route = useRoute();
// 错误消息状态
const errorMessage = ref<string | null>(null);

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应在6-20个字符之间', trigger: 'blur' },
  ],
};

// 检查URL中的错误信息
onMounted(() => {
  const error = route.query.error as string;
  if (error) {
    ElMessage.error(decodeURIComponent(error));
  }
  
  // 检查并清理过期的认证数据
  const token = localStorage.getItem('access_token');
  const tokenExpireTime = localStorage.getItem('token_expire_time');
  
  if (token && tokenExpireTime) {
    const expireTime = parseInt(tokenExpireTime);
    if (Date.now() > expireTime) {
      // 令牌已过期，清除所有认证数据
      userStore.logout();
      ElMessage.warning('登录已过期，请重新登录');
    }
  }
});

const handleLogin = async () => {
  if (!loginFormRef.value) return;

  try {
    loading.value = true;
    errorMessage.value = null; // 清除之前的错误信息
    await loginFormRef.value.validate();

    console.log('开始登录尝试，用户名:', loginForm.value.username);
    try {
      // 使用解构出来的login函数
      const loginSuccess = await login(loginForm.value.username, loginForm.value.password);
      console.log('登录API调用成功:', loginSuccess);

      if (!loginSuccess) {
        throw new Error('登录失败：服务器返回无效的响应');
      }

      // 如果选择了"记住我"，保存用户名
      if (rememberMe.value) {
        storage.set('remembered_username', loginForm.value.username);
      } else {
        storage.remove('remembered_username');
      }

      // 确保用户状态更新到store
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('登录成功但无法获取令牌，请刷新页面重试');
      }
      
      let userInfoData = null;
      try {
        const userInfoStr = localStorage.getItem('user_info');
        userInfoData = userInfoStr ? JSON.parse(userInfoStr) : null;
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
      
      // 更新Pinia store中的用户状态
      userStore.$patch({
        token: token,
        userInfo: userInfoData || {}
      });
      
      console.log('已更新用户store:', {
        token: token ? token.substring(0, 10) + '...' : null,
        userInfo: userInfoData ? '已加载' : '未加载'
      });

      // 启动token刷新定时器
      userStore.startTokenRefresh();

      // 等待一小段时间确保状态同步后再处理跳转
      setTimeout(() => {
        // 处理登录成功
        handleLoginSuccess();
      }, 300);
    } catch (loginError: any) {
      console.error('登录API调用失败:', loginError);
      // 处理具体的登录错误
      if (loginError.response) {
        // 服务器响应了但返回错误
        const status = loginError.response.status;
        if (status === 401) {
          errorMessage.value = '用户名或密码错误';
        } else if (status === 403) {
          errorMessage.value = '您的账号已被禁用';
        } else if (status === 429) {
          errorMessage.value = '登录尝试次数过多，请稍后再试';
        } else if (loginError.response.data?.detail) {
          errorMessage.value = loginError.response.data.detail;
        } else {
          errorMessage.value = `服务器错误 (${status})，请稍后重试`;
        }
      } else if (loginError.request) {
        // 发出了请求但没有收到响应
        console.error('未收到服务器响应:', loginError.request);
        errorMessage.value = '无法连接到服务器，请检查网络连接';
      } else {
        // 请求设置触发的错误
        errorMessage.value = loginError.message || '登录失败，请稍后重试';
      }
      
      // 显示错误消息提示
      ElMessage.error(errorMessage.value || '登录失败');
      loading.value = false;
    }
  } catch (formError: any) {
    // 表单验证错误
    console.error('表单验证失败:', formError);
    ElMessage.error('请检查输入的信息是否正确');
    loading.value = false;
  }
};

const goToRegister = () => {
  router.push('/auth/register');
};

const goToForgotPassword = () => {
  router.push('/auth/forgot-password');
};

// 添加处理登录成功的方法
const handleLoginSuccess = () => {
  // 获取令牌和用户信息，确认登录状态
  const token = localStorage.getItem('access_token');
  
  // 如果没有找到token，显示错误
  if (!token) {
    console.error('找不到有效的access_token');
    ElMessage.error('登录异常：无法获取认证令牌');
    return;
  }
  
  // 获取用户信息并确定重定向目标
  const userInfoStr = localStorage.getItem('user_info');
  let userInfo;
  try {
    userInfo = userInfoStr ? JSON.parse(userInfoStr) : null;
  } catch (e) {
    console.error('解析用户信息失败:', e);
    userInfo = null;
  }
  
  // 根据角色决定跳转目标
  const isAdmin = userInfo?.roles?.includes('admin');
  
  // 优先使用URL中的redirect参数，如果没有则使用默认路径
  const redirectParam = route.query.redirect as string;
  const redirectPath = redirectParam || (isAdmin ? '/admin/dashboard' : '/product/list');
  
  console.log('登录成功，用户信息:', userInfo);
  console.log('用户角色:', userInfo?.roles, '是否管理员:', isAdmin);
  console.log('将跳转到:', redirectPath);
  
  // 显示加载状态
  loading.value = true;
  
  // 立即进行跳转而不是使用延时
  try {
    // 使用router进行跳转，不使用window.location
    router.push(redirectPath);
    console.log('已通过router.push跳转到:', redirectPath);
    ElMessage.success('登录成功');
  } catch (error) {
    console.error('导航过程出错:', error);
    loading.value = false;
    ElMessage.error('跳转失败，请重试');
    
    // 如果router.push失败，尝试使用window.location
    console.log('尝试使用window.location进行跳转');
    const baseUrl = window.location.origin;
    const fullPath = baseUrl + redirectPath;
    window.location.href = fullPath;
  }
};
</script>

<style scoped>
.login-container {
  width: 100%;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
}

.card-header {
  text-align: center;
}

.header-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin: 0 0 8px;
}

.header-subtitle {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin: 0;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.register-link {
  text-align: center;
  margin-top: 16px;
  color: var(--text-color-regular);
  font-size: 14px;
}

:deep(.el-checkbox__label) {
  color: var(--text-color-regular);
}

:deep(.el-link) {
  font-size: 14px;
}

.login-button {
  width: 100%;
  height: 40px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  padding-bottom: 8px;
}

:deep(.el-input__wrapper) {
  box-shadow: none;
  border: 1px solid var(--auth-input-border);
  border-radius: 4px;
  padding: 0 12px;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--color-primary);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: var(--auth-input-focus-shadow);
}

:deep(.el-input__inner) {
  height: 40px;
  line-height: 40px;
}

:deep(.el-input__prefix) {
  font-size: 16px;
  color: var(--text-color-placeholder);
}
</style>

