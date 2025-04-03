import { ref, onMounted, onUnmounted } from 'vue';
import type { Ref } from 'vue';

export interface FetchingOptions<T> {
  immediate?: boolean;
  initialData?: T;
  refreshInterval?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useDataFetching<T>(
  fetchFn: () => Promise<T>,
  options: FetchingOptions<T> = {}
) {
  // 默认选项
  const defaultOptions: FetchingOptions<T> = {
    immediate: true,
    initialData: undefined,
    refreshInterval: 0,
    onSuccess: () => {},
    onError: () => {},
  };

  // 合并选项
  const mergedOptions = { ...defaultOptions, ...options };

  // 状态
  const data = ref<T | undefined>(mergedOptions.initialData) as Ref<T | undefined>;
  const loading = ref(false);
  const error = ref<Error | null>(null);
  const lastFetchTime = ref<number | null>(null);
  const intervalId = ref<number | null>(null);

  // 加载数据方法
  const fetchData = async () => {
    loading.value = true;
    error.value = null;
    
    try {
      const result = await fetchFn();
      data.value = result;
      lastFetchTime.value = Date.now();
      
      if (mergedOptions.onSuccess) {
        mergedOptions.onSuccess(result);
      }
      
      return result;
    } catch (err) {
      error.value = err as Error;
      
      if (mergedOptions.onError) {
        mergedOptions.onError(err as Error);
      }
      
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 刷新数据
  const refresh = () => {
    return fetchData();
  };

  // 设置定时刷新
  const setupInterval = () => {
    if (mergedOptions.refreshInterval && mergedOptions.refreshInterval > 0) {
      clearInterval(intervalId.value as number);
      intervalId.value = window.setInterval(() => {
        fetchData().catch(() => {});
      }, mergedOptions.refreshInterval);
    }
  };

  // 清除定时刷新
  const clearRefreshInterval = () => {
    if (intervalId.value !== null) {
      clearInterval(intervalId.value);
      intervalId.value = null;
    }
  };

  // 组件挂载时加载数据
  onMounted(() => {
    if (mergedOptions.immediate) {
      fetchData().catch(() => {});
    }
    setupInterval();
  });

  // 组件卸载时清除定时器
  onUnmounted(() => {
    clearRefreshInterval();
  });

  return {
    // 状态
    data,
    loading,
    error,
    lastFetchTime,
    
    // 方法
    fetchData,
    refresh,
    clearRefreshInterval,
  };
} 