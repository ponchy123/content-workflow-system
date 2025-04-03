import { computed } from 'vue';
import { useSettingsStore } from '@/stores/settings';

export function useTheme() {
  const settingsStore = useSettingsStore();
  const currentTheme = computed(() => settingsStore.theme);

  const toggleTheme = () => {
    settingsStore.setTheme(currentTheme.value === 'dark' ? 'light' : 'dark');
  };

  return {
    currentTheme,
    toggleTheme,
  };
} 