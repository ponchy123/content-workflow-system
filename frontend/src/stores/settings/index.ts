import { defineStore } from 'pinia';
import { ref, watch, computed, nextTick } from 'vue';
import { useLocalStorage, usePreferredDark, useNetwork } from '@vueuse/core';
import { ElMessage } from 'element-plus';
import type { LocaleType } from '@/i18n';
import { setLocale, loadLocaleMessages } from '@/i18n';
import http from '@/api/core/request';
import type { ConfigItem } from '@/types/config';
import { 
  LOCALE_CONFIG, 
  THEME_DEFAULTS, 
  UI_DEFAULTS, 
  NOTIFICATION_DEFAULTS 
} from './constants';
import type { 
  ThemeSettings, 
  LanguageSettings, 
  UiSettings, 
  NotificationSettings,
  ConfigState
} from './types';

// 导入axios
import axios from 'axios';

export const useSettingsStore = defineStore('settings', () => {
  // 主题设置
  const theme = useLocalStorage<ThemeSettings['theme']>('freight-theme', 'auto');
  const isDark = usePreferredDark();
  const actualTheme = computed(() => {
    return theme.value === 'auto' ? (isDark.value ? 'dark' : 'light') : theme.value;
  });
  
  // 语言设置
  const language = useLocalStorage<LocaleType>('freight-language', 'zh-CN');
  
  // UI设置
  const uiSettings = useLocalStorage<UiSettings>('freight-ui-settings', UI_DEFAULTS);
  
  // 通知设置
  const notificationSettings = useLocalStorage<NotificationSettings>(
    'freight-notification-settings', 
    NOTIFICATION_DEFAULTS
  );
  
  // 已完成的引导
  const guidesCompleted = useLocalStorage<string[]>('freight-guides-completed', []);
  
  // 加载状态
  const loadingStates = ref(new Map<string, boolean>());
  
  // 网络状态
  const network = useNetwork();
  const isOnline = computed(() => network.isOnline.value);
  const isReconnecting = ref(false);
  const reconnectAttempts = ref(0);
  
  // 系统配置管理
  const configs = ref<ConfigItem[]>([]);
  const configLoading = ref(false);
  
  // 主题切换
  const toggleTheme = async () => {
    theme.value = actualTheme.value === 'light' ? 'dark' : 'light';
    await applyThemeTransition();
  };
  
  // 应用主题过渡效果
  const applyThemeTransition = async () => {
    document.documentElement.classList.add('theme-transition');
    document.documentElement.setAttribute('data-theme', actualTheme.value);
    await nextTick();
    document.documentElement.classList.remove('theme-transition');
  };
  
  // 更新语言
  const updateLanguage = async (newLanguage: LocaleType) => {
    try {
      await loadLocaleMessages(newLanguage);
      setLocale(newLanguage);
      language.value = newLanguage;
      ElMessage.success(`语言已切换到${newLanguage}`);
    } catch (error) {
      ElMessage.error(`切换语言失败: ${error}`);
    }
  };
  
  // 日期格式化
  const formatDate = (
    date: Date | string | number,
    format: keyof typeof LOCALE_CONFIG.DATE_FORMATS = 'short',
  ): string => {
    const dateObj = new Date(date);
    return new Intl.DateTimeFormat(
      language.value, 
      LOCALE_CONFIG.DATE_FORMATS[format]
    ).format(dateObj);
  };
  
  // 设置加载状态
  const setLoading = (key: string, isLoading: boolean) => {
    loadingStates.value.set(key, isLoading);
  };
  
  // 检查加载状态
  const isLoading = (key: string) => loadingStates.value.get(key) || false;
  
  // 监听主题变化
  watch(
    actualTheme,
    (newTheme) => {
      document.documentElement.setAttribute('data-theme', newTheme);
    },
    { immediate: true }
  );
  
  // 加载设置
  const loadSettings = async () => {
    setLoading('settings', true);
    try {
      // 应用当前主题
      document.documentElement.setAttribute('data-theme', actualTheme.value);
      
      // 加载配置
      await fetchConfigs();
      
      // 设置语言
      if (language.value) {
        await loadLocaleMessages(language.value);
        setLocale(language.value);
      }
      
      return true;
    } catch (error) {
      console.error('加载设置失败:', error);
      ElMessage.error('加载应用设置失败，请刷新页面重试');
      throw error;
    } finally {
      setLoading('settings', false);
    }
  };
  
  // 获取所有配置
  const fetchConfigs = async () => {
    configLoading.value = true;
    try {
      console.log('尝试获取配置...');
      
      try {
        console.log('使用axios请求');
        const response = await axios.get('/api/v1/configs', {
          headers: {
            'Accept': 'application/json'
          },
          withCredentials: true
        });
        
        console.log('配置获取成功:', response.data);
        configs.value = response.data;
        return;
      } catch (error) {
        console.warn('axios请求失败，尝试备用方法', error);
        
        // 使用模拟数据作为备用
        console.log('使用默认配置');
        configs.value = [{
          id: 'fallback',
          key: 'apiUrl',
          value: '/api/v1/',
          type: 'text',
          description: '后端API基础URL (备用值)',
          status: true
        }];
      }
    } catch (error) {
      console.error('获取配置失败:', error);
      throw error;
    } finally {
      configLoading.value = false;
    }
  };

  // 添加配置
  const addConfig = async (config: Omit<ConfigItem, 'id'>) => {
    try {
      const response = await http.post('/api/v1/configs', config);
      configs.value.push(response.data);
      return response.data;
    } catch (error) {
      console.error('添加配置失败:', error);
      throw error;
    }
  };

  // 更新配置
  const updateConfig = async (id: string, config: Partial<ConfigItem>) => {
    try {
      const response = await http.put(`/api/v1/configs/${id}`, config);
      const index = configs.value.findIndex(item => item.id === id);
      if (index !== -1) {
        configs.value[index] = response.data;
      }
      return response.data;
    } catch (error) {
      console.error('更新配置失败:', error);
      throw error;
    }
  };

  // 删除配置
  const deleteConfig = async (id: string) => {
    try {
      await http.delete(`/api/v1/configs/${id}`);
      const index = configs.value.findIndex(item => item.id === id);
      if (index !== -1) {
        configs.value.splice(index, 1);
      }
    } catch (error) {
      console.error('删除配置失败:', error);
      throw error;
    }
  };

  // 获取配置值
  const getConfigValue = (key: string) => {
    const config = configs.value.find(item => item.key === key);
    return config?.value;
  };

  // 批量更新配置
  const batchUpdateConfigs = async (updates: Array<{ id: string; value: any }>) => {
    try {
      const response = await http.put('/api/v1/configs/batch', { updates });
      updates.forEach(update => {
        const config = configs.value.find(item => item.id === update.id);
        if (config) {
          config.value = update.value;
        }
      });
      return response.data;
    } catch (error) {
      console.error('批量更新配置失败:', error);
      throw error;
    }
  };

  return {
    // 状态
    theme,
    language,
    uiSettings,
    notificationSettings,
    guidesCompleted,
    isOnline,
    isReconnecting,
    reconnectAttempts,
    
    // 计算属性
    actualTheme,
    
    // 方法
    toggleTheme,
    updateLanguage,
    formatDate,
    setLoading,
    isLoading,
    loadSettings,

    // 配置管理
    configs,
    configLoading,
    fetchConfigs,
    addConfig,
    updateConfig,
    deleteConfig,
    getConfigValue,
    batchUpdateConfigs,
  };
}); 