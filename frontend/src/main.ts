import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import 'element-plus/dist/index.css';
import '@/styles/base.css';

import App from './App.vue';
import router from './router';
import { i18n, setupI18n } from './i18n';
import { vPermission, vRole } from './utils/validation/permission';
import { setupRouterGuard } from './router/guard';
import { useUserStore } from './stores/user';
import { useSettingsStore } from './stores/settings';

const bootstrap = async () => {
  const app = createApp(App);
  const pinia = createPinia();

  // 初始化 Pinia
  app.use(pinia);

  // 初始化其他插件
  app.use(ElementPlus);

  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }

  // 初始化 i18n
  setupI18n(app);

  try {
    // 初始化设置
    const settingsStore = useSettingsStore();
    await settingsStore.loadSettings();

    // 初始化用户状态
    const userStore = useUserStore();
    await userStore.initialize();

    // 注册权限指令
    app.directive('permission', vPermission);
    app.directive('role', vRole);

    // 设置路由守卫
    setupRouterGuard(router);
    app.use(router);

    // 挂载应用
    app.mount('#app');
  } catch (error) {
    console.error('Failed to initialize app:', error);
    // 即使初始化失败，也要挂载应用以显示错误信息
    app.use(router);
    app.mount('#app');
  }
};

// 启动应用
bootstrap().catch((error) => {
  console.error('Failed to bootstrap app:', error);
  // 在这里可以显示一个全局错误提示
  const app = createApp(App);
  app.use(createPinia());
  app.use(ElementPlus);
  app.use(router);
  app.mount('#app');
});
