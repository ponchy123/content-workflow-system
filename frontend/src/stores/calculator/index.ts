import { defineStore } from 'pinia';
import { ref, computed, onUnmounted } from 'vue';
import type { CalculationRequest, CalculationResult } from '@/types/calculator';
import { calculateFreight, calculateBatch } from '@/api/calculator/index';
import { useLocalStorage } from '@vueuse/core';
import type { CalculationHistory } from '@/types/calculator';
import { useHistoryStore } from './history';

// 历史记录配置
const HISTORY_CONFIG = {
  MAX_ITEMS: 100, // 最大保存数量
  FAVORITE_MAX_ITEMS: 50, // 最大收藏数量
  RECENT_MAX_ITEMS: 20, // 最近使用数量
};

// 创建计算 Web Worker
const calculationWorker = new Worker(new URL('@/workers/calculator.worker.ts', import.meta.url), {
  type: 'module',
});

export const useCalculatorStore = defineStore('calculator', () => {
  // 使用持久化存储
  const history = useLocalStorage<CalculationHistory[]>('calc_history', []);
  const favorites = useLocalStorage<Set<string>>('calc_favorites', new Set());
  const recentSearches = useLocalStorage<string[]>('calc_recent_searches', []);

  // 状态
  const currentResult = ref<CalculationResult | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const sortedHistory = computed(() => {
    return [...history.value].sort((a, b) => b.timestamp - a.timestamp);
  });

  const groupedHistory = computed(() => {
    const groups = new Map<string, CalculationHistory[]>();

    history.value.forEach(item => {
      const date = new Date(item.timestamp).toLocaleDateString();
      if (!groups.has(date)) {
        groups.set(date, []);
      }
      groups.get(date)?.push(item);
    });

    return groups;
  });

  const favoriteHistory = computed(() => {
    return history.value.filter(item => favorites.value.has(item.id));
  });

  // 添加虚拟滚动支持
  const virtualListConfig = {
    itemHeight: 60, // 每个历史记录项的高度
    bufferSize: 5, // 上下缓冲区大小
    pageSize: 20, // 每页加载数量
  };

  // 分页加载历史记录
  const loadHistoryPage = (page: number) => {
    const start = page * virtualListConfig.pageSize;
    const end = start + virtualListConfig.pageSize;
    return sortedHistory.value.slice(start, end);
  };

  // 预加载下一页数据
  const preloadNextPage = computed(() => {
    return (currentPage: number) => {
      const nextPage = currentPage + 1;
      return loadHistoryPage(nextPage);
    };
  });

  // 优化的分组历史记录
  const virtualGroupedHistory = computed(() => {
    const groups = new Map<
      string,
      {
        items: CalculationHistory[];
        total: number;
        loaded: number;
      }
    >();

    history.value.forEach(item => {
      const date = new Date(item.timestamp).toLocaleDateString();
      if (!groups.has(date)) {
        groups.set(date, {
          items: [],
          total: 0,
          loaded: 0,
        });
      }
      const group = groups.get(date)!;
      group.total++;

      // 只加载可见部分
      if (group.items.length < virtualListConfig.pageSize) {
        group.items.push(item);
        group.loaded++;
      }
    });

    return groups;
  });

  // 加载更多分组数据
  const loadMoreGroupItems = (date: string, count: number) => {
    const group = virtualGroupedHistory.value.get(date);
    if (!group || group.loaded >= group.total) return;

    const start = group.loaded;
    const itemsToLoad = history.value
      .filter(item => new Date(item.timestamp).toLocaleDateString() === date)
      .slice(start, start + count);

    group.items.push(...itemsToLoad);
    group.loaded += itemsToLoad.length;
  };

  // 数据预加载
  let preloadTimer: number | null = null;
  const startPreloading = () => {
    if (preloadTimer) return;

    preloadTimer = window.setInterval(() => {
      // 预加载下一页数据
      const currentSize = history.value.length;
      const preloadThreshold = Math.floor(currentSize * 0.8); // 当加载到80%时预加载

      if (currentSize >= preloadThreshold) {
        // 触发预加载
        preloadNextPage.value(Math.floor(currentSize / virtualListConfig.pageSize));
      }
    }, 1000);
  };

  const stopPreloading = () => {
    if (preloadTimer) {
      clearInterval(preloadTimer);
      preloadTimer = null;
    }
  };

  // 初始化时启动预加载
  startPreloading();

  // 在组件卸载时清理
  onUnmounted(() => {
    stopPreloading();
  });

  // Web Worker 消息处理
  calculationWorker.onmessage = event => {
    const { type, data, request } = event.data;
    switch (type) {
      case 'CALCULATION_COMPLETE':
        currentResult.value = data;
        addHistory(data, request);
        loading.value = false;
        break;
      case 'CALCULATION_ERROR':
        console.error('计算错误:', data);
        loading.value = false;
        break;
    }
  };

  // 单个运费计算
  const calculate = async (request: CalculationRequest) => {
    try {
      loading.value = true;

      // 添加到最近搜索
      addRecentSearch(JSON.stringify(request));

      // 使用 Web Worker 进行计算
      calculationWorker.postMessage({
        type: 'CALCULATE',
        data: request,
      });

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('计算超时'));
          loading.value = false;
        }, 30000);

        calculationWorker.onmessage = event => {
          clearTimeout(timeout);
          const { type, data } = event.data;
          if (type === 'CALCULATION_COMPLETE') {
            resolve(data);
          } else {
            reject(new Error(data));
          }
          loading.value = false;
        };
      });
    } catch (error) {
      console.error('计算运费失败:', error);
      loading.value = false;
      throw error;
    }
  };

  // 添加计算历史
  const addHistory = (result: CalculationResult, request: CalculationRequest) => {
    const historyItem: CalculationHistory = {
      id: generateHistoryId(),
      request,
      ...result,
      timestamp: Date.now(),
    };

    history.value.unshift(historyItem);

    // 限制历史记录数量
    if (history.value.length > HISTORY_CONFIG.MAX_ITEMS) {
      // 保留收藏的记录
      const favoriteIds = new Set(favorites.value);
      const nonFavorites = history.value.filter(item => !favoriteIds.has(item.id));
      const favoritesItems = history.value.filter(item => favoriteIds.has(item.id));

      // 删除非收藏的旧记录
      history.value = [
        ...favoritesItems,
        ...nonFavorites.slice(0, HISTORY_CONFIG.MAX_ITEMS - favoritesItems.length),
      ];
    }

    return historyItem.id;
  };

  // 添加到最近搜索
  const addRecentSearch = (search: string) => {
    const index = recentSearches.value.indexOf(search);
    if (index > -1) {
      recentSearches.value.splice(index, 1);
    }
    recentSearches.value.unshift(search);

    // 限制最近搜索数量
    if (recentSearches.value.length > HISTORY_CONFIG.RECENT_MAX_ITEMS) {
      recentSearches.value = recentSearches.value.slice(0, HISTORY_CONFIG.RECENT_MAX_ITEMS);
    }
  };

  // 切换收藏状态
  const toggleFavorite = (id: string) => {
    if (favorites.value.has(id)) {
      favorites.value.delete(id);
    } else {
      // 检查是否超过收藏上限
      if (favorites.value.size >= HISTORY_CONFIG.FAVORITE_MAX_ITEMS) {
        const oldestFavorite = Array.from(favorites.value)[0];
        favorites.value.delete(oldestFavorite);
      }
      favorites.value.add(id);
    }
  };

  // 清除历史记录
  const clearHistory = (keepFavorites = true) => {
    if (keepFavorites) {
      history.value = history.value.filter(item => favorites.value.has(item.id));
    } else {
      history.value = [];
      favorites.value.clear();
    }
  };

  // 删除单条历史记录
  const deleteHistory = (id: string) => {
    history.value = history.value.filter(item => item.id !== id);
    favorites.value.delete(id);
  };

  // 导出历史记录
  const exportHistory = () => {
    const exportData = {
      history: history.value,
      favorites: Array.from(favorites.value),
      recentSearches: recentSearches.value,
      exportDate: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `calculation-history-${new Date().toISOString()}.json`;
    a.click();

    URL.revokeObjectURL(url);
  };

  // 导入历史记录
  const importHistory = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);

      if (data.history && Array.isArray(data.history)) {
        history.value = data.history;
      }

      if (data.favorites && Array.isArray(data.favorites)) {
        favorites.value = new Set(data.favorites);
      }

      if (data.recentSearches && Array.isArray(data.recentSearches)) {
        recentSearches.value = data.recentSearches;
      }

      return true;
    } catch (err) {
      console.error('导入历史记录失败:', err);
      return false;
    }
  };

  // 生成历史记录ID
  const generateHistoryId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  return {
    history,
    favorites,
    recentSearches,
    currentResult,
    loading,
    error,
    sortedHistory,
    groupedHistory,
    favoriteHistory,
    addHistory,
    addRecentSearch,
    toggleFavorite,
    clearHistory,
    deleteHistory,
    exportHistory,
    importHistory,
    calculate,
    virtualListConfig,
    loadHistoryPage,
    preloadNextPage,
    virtualGroupedHistory,
    loadMoreGroupItems,
  };
});
