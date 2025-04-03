<!-- ThemeProvider.vue -->
<template>
  <div
    class="theme-provider"
    :class="[`theme-${currentTheme}`, { 'theme-transition': enableTransition }]"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings';
import { computed, onMounted } from 'vue';

interface Props {
  enableTransition?: boolean;
}

withDefaults(defineProps<Props>(), {
  enableTransition: true,
});

const settingsStore = useSettingsStore();
const currentTheme = computed(() => settingsStore.currentTheme);

onMounted(() => {
  document.documentElement.classList.toggle('dark', currentTheme.value === 'dark');
});
</script>

<style>
.theme-provider {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.theme-light {
  color-scheme: light;
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

.theme-dark {
  color-scheme: dark;
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

.theme-transition {
  transition: all 0.3s ease-in-out;
}

:root {
  --transition-duration: 0.3s;
}

/* Light theme variables */
.theme-light {
  --el-bg-color: #ffffff;
  --el-bg-color-overlay: #ffffff;
  --el-text-color-primary: #303133;
  --el-text-color-regular: #606266;
  --el-text-color-secondary: #909399;
  --el-border-color-base: #dcdfe6;
  --el-border-color-light: #e4e7ed;
  --el-fill-color-blank: #ffffff;
}

/* Dark theme variables */
.theme-dark {
  --el-bg-color: #141414;
  --el-bg-color-overlay: #1d1e1f;
  --el-text-color-primary: #ffffff;
  --el-text-color-regular: #e5eaf3;
  --el-text-color-secondary: #a3a6ad;
  --el-border-color-base: #434343;
  --el-border-color-light: #363637;
  --el-fill-color-blank: #141414;
}
</style>
