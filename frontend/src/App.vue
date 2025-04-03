<template>
  <el-config-provider :locale="locale">
    <ThemeProvider>
      <router-view />
    </ThemeProvider>
  </el-config-provider>
</template>

<script setup lang="ts">
  import { onMounted } from 'vue';
  import { useSettingsStore } from '@/stores/settings';
  import zhCn from 'element-plus/dist/locale/zh-cn.mjs';
  import enUs from 'element-plus/dist/locale/en.mjs';
  import { computed } from 'vue';
  import ThemeProvider from '@/components/common/settings/ThemeProvider.vue';
  import { ElConfigProvider } from 'element-plus';
  import { useUserStore } from '@/stores/user';
  import { TOKEN_KEY } from '@/types/auth';

  const settingsStore = useSettingsStore();

  // Element Plus 语言配置
  const locale = computed(() => {
    return settingsStore.language === 'zh-CN' ? zhCn : enUs;
  });

  // 应用启动时同步token
  onMounted(async () => {
    // 初始化设置
    await settingsStore.loadSettings();
    
    console.log('应用启动，初始化认证状态...');
    
    // 检查token
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      console.log('发现有效的token，初始化用户状态');
      
      // 初始化用户状态
      const userStore = useUserStore();
      if (userStore.isLoggedIn) {
        console.log('用户已登录，启动token刷新机制');
        userStore.startTokenRefresh();
      }
    } else {
      console.log('未找到有效的token');
    }
  });
</script>

<style>
  @import '@/styles/base.css';

  #app {
    font-family: var(--el-font-family);
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color);
  }

  /* 暗色模式样式 */
  html.dark {
    background-color: var(--el-bg-color-dark);
    color: var(--el-text-color-primary);
  }

  html.dark #app {
    background-color: var(--el-bg-color-dark);
  }

  /* 基础样式 */
  html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    width: 100%;
    overflow: hidden;
  }

  /* 路由视图容器 */
  .router-view {
    flex: 1;
    overflow-y: auto;
    position: relative;
  }
</style>
