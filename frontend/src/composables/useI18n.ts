import { computed } from 'vue';
import { useSettingsStore } from '@/stores/settings';
import { ElMessage } from 'element-plus';
import type { LocaleType } from '@/i18n';

export function useI18n() {
  const settingsStore = useSettingsStore();

  const currentLanguage = computed(() => settingsStore.language);

  const setLanguage = async (lang: LocaleType) => {
    try {
      await settingsStore.updateLanguage(lang);
      ElMessage.success('语言切换成功');
    } catch (error) {
      console.error('Failed to change language:', error);
      ElMessage.error('语言切换失败');
    }
  };

  return {
    currentLanguage,
    setLanguage,
  };
} 