<template>
  <div class="error-container">
    <div class="error-content">
      <h1 class="error-code">500</h1>
      <h2 class="error-title">服务器错误</h2>
      <p class="error-message">服务器遇到了错误，请稍后再试</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
      <el-button @click="reload">刷新页面</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const goHome = () => {
  router.push('/');
};

const reload = () => {
  window.location.reload();
};
</script>

<style scoped>
.error-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.error-content {
  max-width: 500px;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  line-height: 1;
  margin: 0;
  color: var(--el-color-error);
  font-weight: 700;
}

.error-title {
  font-size: 32px;
  margin: 16px 0;
  color: var(--el-text-color-primary);
}

.error-message {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 32px;
}
</style> 