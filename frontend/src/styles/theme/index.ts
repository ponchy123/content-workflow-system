import { ref, watch } from 'vue';
import { useStorage } from '@vueuse/core';
import type { ThemeMode } from './types';
import { lightTheme, darkTheme } from './themes';
import { generateCssVariables, applyCssVariables, isDarkMode, watchSystemTheme } from './utils';

export * from './types';
export * from './themes';
export * from './utils';

// 导出默认主题配置
export { lightTheme as defaultTheme } from './themes';

export function useTheme() {
  const themeMode = useStorage<ThemeMode>('theme-mode', 'system');
  const systemDark = ref(isDarkMode());

  // 监听系统主题变化
  const stopWatchSystem = watchSystemTheme(dark => {
    systemDark.value = dark;
  });

  // 应用主题
  const applyTheme = (mode: ThemeMode = themeMode.value) => {
    const isDark = mode === 'system' ? systemDark.value : mode === 'dark';
    const theme = isDark ? darkTheme : lightTheme;
    const cssVars = generateCssVariables(theme);
    applyCssVariables(cssVars);
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  };

  // 监听主题模式变化
  watch(
    [themeMode, systemDark],
    () => {
      applyTheme();
    },
    { immediate: true },
  );

  // 切换主题
  const toggleTheme = () => {
    if (themeMode.value === 'light') {
      themeMode.value = 'dark';
    } else if (themeMode.value === 'dark') {
      themeMode.value = 'system';
    } else {
      themeMode.value = 'light';
    }
  };

  // 组件卸载时清理监听器
  const dispose = () => {
    stopWatchSystem();
  };

  return {
    themeMode,
    systemDark,
    applyTheme,
    toggleTheme,
    dispose,
  };
}
