<template>
  <div class="reset-password-container">
    <el-card class="reset-password-card">
      <template #header>
        <div class="card-header">
          <h2 class="header-title">重置密码</h2>
          <p class="header-subtitle">请设置您的新密码</p>
        </div>
      </template>
      
      <el-form
        v-if="!submitSuccess && !resetError"
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleSubmit"
      >
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            placeholder="请输入新密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="submit-button"
            @click="handleSubmit"
          >
            {{ loading ? '提交中...' : '重置密码' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 提交成功提示 -->
      <div v-if="submitSuccess" class="success-message">
        <el-icon class="success-icon"><Check /></el-icon>
        <p>密码重置成功！</p>
        <p>您可以使用新密码登录您的账户了。</p>
        <el-button type="primary" class="login-button" @click="goToLogin">
          去登录
        </el-button>
      </div>
      
      <!-- 重置错误提示 -->
      <div v-if="resetError" class="error-message">
        <el-icon class="error-icon"><WarningFilled /></el-icon>
        <p>重置链接无效或已过期</p>
        <p>请重新发起密码重置请求。</p>
        <el-button type="primary" class="forgot-button" @click="goToForgotPassword">
          忘记密码
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Lock, Check, WarningFilled } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { useAuth } from '@/composables/useAuth';

const route = useRoute();
const router = useRouter();
const formRef = ref<FormInstance>();
const loading = ref(false);
const submitSuccess = ref(false);
const resetError = ref(false);
const { resetPassword } = useAuth();

// 从URL参数中获取uid和token
const uid = ref(route.params.uid as string);
const token = ref(route.params.token as string);

// 表单数据
const form = ref({
  newPassword: '',
  confirmPassword: ''
});

// 表单验证规则
const rules = ref<FormRules>({
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.value.newPassword) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
});

// 检查URL参数是否有效
onMounted(() => {
  if (!uid.value || !token.value) {
    resetError.value = true;
    ElMessage.error('重置链接无效');
  }
});

const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    loading.value = true;
    
    // 调用API重置密码
    const result = await resetPassword(
      uid.value,
      token.value,
      form.value.newPassword,
      form.value.confirmPassword
    );
    
    // 显示成功消息
    submitSuccess.value = true;
    ElMessage.success('密码重置成功');
    
  } catch (error: any) {
    console.error('Failed to reset password:', error);
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail);
      if (error.response.status === 400) {
        resetError.value = true;
      }
    } else {
      ElMessage.error(error.message || '重置失败，请稍后重试');
    }
  } finally {
    loading.value = false;
  }
};

const goToLogin = () => {
  router.push('/auth/login');
};

const goToForgotPassword = () => {
  router.push('/auth/forgot-password');
};
</script>

<style scoped>
.reset-password-container {
  width: 100%;
  padding: 20px;
}

.reset-password-card {
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

.submit-button,
.login-button,
.forgot-button {
  width: 100%;
  margin-top: 16px;
}

.success-message,
.error-message {
  text-align: center;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.success-message {
  color: #67c23a;
}

.error-message {
  color: #f56c6c;
}

.success-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

p {
  margin: 8px 0;
}
</style> 