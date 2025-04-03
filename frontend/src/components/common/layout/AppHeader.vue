<template>
  <el-header class="app-header">
    <!-- 左侧区域 -->
    <div class="app-header__left">
      <!-- 折叠按钮 -->
      <el-button
        class="app-header__collapse-btn"
        :icon="isCollapsed ? 'Expand' : 'Fold'"
        @click="$emit('toggle-sidebar')"
      />
      <div class="app-header__logo">
        <!-- 临时移除 logo 图片，使用文字替代 -->
        <span class="logo-text">运费计算系统</span>
      </div>
    </div>

    <!-- 右侧区域 -->
    <div class="app-header__right">
      <!-- 语言切换 -->
      <el-dropdown trigger="click" @command="handleLanguageChange">
        <el-button class="language-btn">
          <el-icon><Setting /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN">简体中文</el-dropdown-item>
            <el-dropdown-item command="en-US">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 主题切换 -->
      <el-button class="theme-btn" @click="toggleTheme">
        <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
      </el-button>

      <!-- 用户菜单 -->
      <el-dropdown trigger="click" @command="$emit('command', $event)">
        <div class="user-info">
          <el-avatar :size="32" :src="avatar">{{ username?.charAt(0) }}</el-avatar>
          <span class="username">{{ username }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人资料</el-dropdown-item>
            <el-dropdown-item command="settings">系统设置</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useSettingsStore } from '@/stores/settings';
import { Moon, Sunny, Setting } from '@element-plus/icons-vue';

interface Props {
  username?: string;
  avatar?: string;
  isCollapsed?: boolean;
}

withDefaults(defineProps<Props>(), {
  username: '',
  avatar: '',
  isCollapsed: false,
});

defineEmits<{
  (e: 'toggle-sidebar'): void;
  (e: 'command', command: string): void;
}>();

type Language = 'zh-CN' | 'en-US';

const settingsStore = useSettingsStore();
const isDark = computed(() => settingsStore.currentTheme === 'dark');

const toggleTheme = () => {
  settingsStore.toggleTheme();
};

const handleLanguageChange = (lang: Language) => {
  settingsStore.updateLanguage(lang);
};
</script>

<style lang="scss" scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height, 60px);
  padding: 0 20px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  box-shadow: var(--el-box-shadow-light);
  position: relative;
  z-index: 1000;

  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  &__logo {
    display: flex;
    align-items: center;
    gap: 8px;

    .logo-img {
      height: 32px;
      width: auto;
    }

    .logo-text {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      white-space: nowrap;
    }
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;

  &:hover {
    background-color: var(--el-fill-color-light);
  }

  .username {
    font-size: 14px;
    color: var(--el-text-color-primary);
    margin-left: 8px;
  }
}

.language-btn,
.theme-btn {
  padding: 8px;
  border: none;
  background: none;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: color 0.3s;

  &:hover {
    color: var(--el-text-color-primary);
  }
}
</style>
