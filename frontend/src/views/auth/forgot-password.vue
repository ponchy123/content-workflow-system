<template>
  <div class="forgot-password-container">
    <el-card class="forgot-password-card">
      <template #header>
        <div class="card-header">
          <h2 class="header-title">找回密码</h2>
          <p class="header-subtitle">我们将向您的邮箱发送重置密码的链接</p>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleSubmit"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入您的邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="submit-button"
            @click="handleSubmit"
          >
            {{ loading ? '提交中...' : '发送重置链接' }}
          </el-button>
        </el-form-item>
        
        <div class="back-to-login">
          <el-link type="primary" @click="goBackToLogin">返回登录</el-link>
        </div>
      </el-form>
      
      <!-- 提交成功提示 -->
      <div v-if="submitSuccess" class="success-message">
        <el-icon class="success-icon"><Check /></el-icon>
        <p>重置密码链接已发送至您的邮箱，请注意查收。</p>
        <p class="note">如未收到邮件，请检查垃圾邮件文件夹或稍后再试。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Message, Check } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { useAuth } from '@/composables/useAuth';

const formRef = ref<FormInstance>();
const form = ref({
  email: '',
});
const loading = ref(false);
const submitSuccess = ref(false);
const router = useRouter();
const { forgotPassword } = useAuth();

// 表单验证规则
const rules = ref<FormRules>({
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
});

const handleSubmit = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    loading.value = true;
    
    // 这里需要调用API发送重置链接
    const result = await forgotPassword(form.value.email);
    
    // 显示成功消息
    submitSuccess.value = true;
    
  } catch (error: any) {
    console.error('Failed to send reset link:', error);
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail);
    } else {
      ElMessage.error(error.message || '发送失败，请稍后重试');
    }
  } finally {
    loading.value = false;
  }
};

const goBackToLogin = () => {
  router.push('/auth/login');
};
</script>

<style scoped>
.forgot-password-container {
  width: 100%;
  padding: 20px;
}

.forgot-password-card {
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

.submit-button {
  width: 100%;
  margin-top: 16px;
}

.back-to-login {
  text-align: center;
  margin-top: 16px;
}

.success-message {
  text-align: center;
  padding: 20px;
  color: #67c23a;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.success-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.note {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-top: 8px;
}
</style> 