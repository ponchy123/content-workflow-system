import { createPinia } from 'pinia';
import { storeToRefs } from 'pinia';

// 创建pinia实例
export const pinia = createPinia();

// 导出产品和设置store
import { useUserStore } from './user';
import { useProductStore } from './product';
import { useSettingsStore } from './settings';

export {
  useUserStore,
  useProductStore,
  useSettingsStore
};

// 工具函数，避免循环依赖
export function getStore(useStore: any) {
  const store = useStore();
  const storeRefs = storeToRefs(store);
  return {
    ...store,
    ...storeRefs,
  };
} 