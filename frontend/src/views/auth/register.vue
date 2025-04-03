<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2 class="header-title">创建账号</h2>
          <p class="header-subtitle">请填写以下信息完成注册</p>
        </div>
      </template>
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="rules"
        label-position="top"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="register-button"
            @click="handleRegister"
          >
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>
        <div class="login-link">
          已有账号？
          <el-link type="primary" @click="goToLogin">立即登录</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock, Message } from '@element-plus/icons-vue';
import type { FormRules } from 'element-plus';

const router = useRouter();
const loading = ref(false);

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});

const validatePass = (rule: any, value: string, callback: Function) => {
  if (value === '') {
    callback(new Error('请输入密码'));
  } else {
    if (registerForm.value.confirmPassword !== '') {
      // 如果确认密码已经输入，则同时验证确认密码
      if (value !== registerForm.value.confirmPassword) {
        callback(new Error('两次输入的密码不一致'));
      }
    }
    callback();
  }
};

const validatePass2 = (rule: any, value: string, callback: Function) => {
  if (value === '') {
    callback(new Error('请再次输入密码'));
  } else if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度不能小于3个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, validator: validatePass, trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' },
  ],
};

// 跳转到登录页面
const goToLogin = () => {
  router.push('/auth/login');
};

// 处理注册
const handleRegister = async () => {
  loading.value = true;
  try {
    // 这里应该调用实际的注册 API
    // 为了演示，我们直接模拟注册成功
    await new Promise(resolve => setTimeout(resolve, 1000));
    ElMessage.success('注册成功，请登录');
    router.push('/auth/login');
  } catch (error) {
    console.error('Registration failed:', error);
    ElMessage.error('注册失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  width: 100%;
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 720px;
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

.login-link {
  text-align: center;
  margin-top: 16px;
  color: var(--text-color-regular);
  font-size: 14px;
}

.register-button {
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

<style scoped>
  .register-view {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--bg-color-page);

    .register-container {
      width: 100%;
      max-width: 720px;
      padding: var(--spacing-extra-large);
      background-color: var(--bg-color);
      border-radius: var(--border-radius-large);
      box-shadow: var(--box-shadow);

      .register-header {
        text-align: center;
        margin-bottom: var(--spacing-large);

        .title {
          font-size: var(--font-size-extra-large);
          font-weight: var(--font-weight-bold);
          color: var(--text-color-primary);
          margin-bottom: var(--spacing-small);
        }

        .subtitle {
          font-size: var(--font-size-base);
          color: var(--text-color-secondary);
        }
      }

      .register-form {
        :deep(.el-form-item) {
          margin-bottom: var(--spacing-large);

          .el-form-item__label {
            color: var(--text-color-regular);
            font-weight: var(--font-weight-medium);
          }

          .el-input__wrapper {
            &.is-focus {
              box-shadow: 0 0 0 1px var(--color-primary) inset;
            }
          }

          .form-tip {
            font-size: var(--font-size-small);
            color: var(--text-color-secondary);
            margin-top: var(--spacing-mini);
          }
        }

        .form-actions {
          margin-top: var(--spacing-extra-large);

          .register-button {
            width: 100%;
            height: 40px;
            font-size: var(--font-size-medium);
          }
        }

        .form-footer {
          margin-top: var(--spacing-base);
          text-align: center;

          .login-link {
            color: var(--color-primary);
            text-decoration: none;

            &:hover {
              color: var(--color-primary-dark);
            }
          }
        }
      }
    }
  }
</style>
