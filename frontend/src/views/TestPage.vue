<template>
  <div class="test-page">
    <h1>测试页面</h1>
    <p class="welcome-text">如果你看到这个页面，说明导航成功了!</p>
    
    <el-alert
      title="登录状态测试"
      type="success"
      :closable="false"
      description="这个页面用于测试登录和导航功能是否正常"
      show-icon
    />
    
    <div class="info-section">
      <h2>用户状态信息</h2>
      <p>当前用户信息:</p>
      <el-descriptions border>
        <el-descriptions-item label="用户名">{{ userInfo?.username || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ userInfo?.roles?.join(', ') || '无角色信息' }}</el-descriptions-item>
        <el-descriptions-item label="登录状态">{{ token ? '已登录' : '未登录' }}</el-descriptions-item>
      </el-descriptions>
      
      <h3>Token信息</h3>
      <el-input
        type="textarea"
        :model-value="String(tokenDisplay)"
        :rows="3"
        readonly
      />
    </div>
    
    <div class="button-group">
      <el-button type="primary" @click="goToDashboard">前往仪表盘</el-button>
      <el-button @click="goHome">返回首页</el-button>
      <el-button type="danger" @click="clearAndLogout">清除凭证并登出</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { storage } from '@/utils/storage';
import { ElMessage } from 'element-plus';

const router = useRouter();
const token = ref(storage.get('token') || localStorage.getItem('token') || '未找到Token');
const userInfo = ref(storage.get('user_info') || JSON.parse(localStorage.getItem('user_info') || '{}'));

const tokenDisplay = computed(() => {
  if (typeof token.value === 'string' && token.value.length > 20) {
    return token.value.substring(0, 10) + '...' + token.value.substring(token.value.length - 10);
  }
  return token.value;
});

onMounted(() => {
  console.log('测试页面加载成功');
  console.log('localStorage中的token:', localStorage.getItem('token'));
  console.log('localStorage中的用户信息:', localStorage.getItem('user_info'));
  
  // 检查token是否有效
  if (!localStorage.getItem('token')) {
    ElMessage.warning('未检测到有效的登录凭证，请重新登录');
  }
});

const goHome = () => {
  router.push('/');
};

const goToDashboard = () => {
  // 根据角色决定去哪个仪表盘
  const isAdmin = userInfo.value?.roles?.includes('admin');
  const path = isAdmin ? '/admin/dashboard' : '/dashboard';
  router.push(path);
};

const clearAndLogout = () => {
  // 清除所有凭证
  localStorage.removeItem('token');
  localStorage.removeItem('user_info');
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user_info');
  storage.remove('token');
  storage.remove('user_info');
  
  // 删除cookie
  document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  
  ElMessage.success('已清除所有登录凭证');
  
  // 重定向到登录页
  setTimeout(() => {
    window.location.href = window.location.origin + '/auth/login';
  }, 1000);
};
</script>

<style scoped>
.test-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  color: var(--el-color-primary);
  margin-bottom: 20px;
}

.welcome-text {
  font-size: 18px;
  margin-bottom: 30px;
}

.info-section {
  margin: 30px 0;
  padding: 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background-color: #f9f9f9;
}

.info-section h2 {
  margin-top: 0;
  color: var(--el-color-primary);
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

h3 {
  margin-top: 20px;
  margin-bottom: 10px;
}
</style> 