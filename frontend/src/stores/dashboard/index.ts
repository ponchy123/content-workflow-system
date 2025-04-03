import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DashboardState } from '../../types/dashboard';
import httpService from '@/api/core/request';

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const loading = ref(false);
  const error = ref<string | null>(null);
  const dashboardData = ref<DashboardState | null>(null);

  // 计算属性
  const isLoading = computed(() => loading.value);
  const hasError = computed(() => error.value !== null);
  const getData = computed(() => dashboardData.value);

  // 方法
  const fetchDashboardData = async () => {
    try {
      loading.value = true;
      error.value = null;
      const { data } = await httpService.get<DashboardState>('/api/dashboard/summary');
      dashboardData.value = data;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取数据失败';
      console.error('获取仪表盘数据失败:', err);
    } finally {
      loading.value = false;
    }
  };

  // 定期刷新数据
  let refreshTimer: number | null = null;

  const startAutoRefresh = (interval = 60000) => { // 默认1分钟刷新一次
    if (refreshTimer) return;
    refreshTimer = window.setInterval(fetchDashboardData, interval);
  };

  const stopAutoRefresh = () => {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  };

  // 组件卸载时清理
  const cleanup = () => {
    stopAutoRefresh();
    resetState();
  };

  const clearError = () => {
    error.value = null;
  };

  const resetState = () => {
    loading.value = false;
    error.value = null;
    dashboardData.value = null;
  };

  return {
    // 状态
    loading,
    error,
    dashboardData,
    
    // 计算属性
    isLoading,
    hasError,
    getData,
    
    // 方法
    fetchDashboardData,
    clearError,
    resetState,
    startAutoRefresh,
    stopAutoRefresh,
    cleanup
  };
}); 