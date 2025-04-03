import { defineStore } from 'pinia';
import { ref } from 'vue';
import { actions } from './actions';
import { getters } from './getters';
import type { ProductState } from './types';

export const useProductStore = defineStore('product', () => {
  // 状态
  const products = ref<ProductState['products']>([]);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  return {
    // 状态
    products,
    loading,
    error,
    
    // Getters
    ...getters,
    
    // Actions
    ...actions,
  };
}); 