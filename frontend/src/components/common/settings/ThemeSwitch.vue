<template>
  <div class="theme-switch">
    <!-- 主题切换按钮 -->
    <el-button
      :type="buttonType"
      :size="size"
      :icon="currentTheme === 'dark' ? 'Sunny' : 'Moon'"
      @click="toggleTheme"
    >
      {{ buttonText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { useTheme } from '@/composables/useTheme';

  interface Props {
    buttonType?: '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text' | 'default';
    size?: 'large' | 'default' | 'small';
    showText?: boolean;
  }

  const props = withDefaults(defineProps<Props>(), {
    buttonType: '',
    size: 'default',
    showText: true,
  });

  const { currentTheme, toggleTheme } = useTheme();

  // 按钮文本
  const buttonText = computed(() => {
    if (!props.showText) return '';
    return currentTheme.value === 'dark' ? '浅色模式' : '深色模式';
  });
</script>

<style scoped>
  .theme-switch {
    display: inline-block;
  }
</style>
