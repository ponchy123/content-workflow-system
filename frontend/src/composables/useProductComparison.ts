import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import type { Product, ProductComparison } from '@/types/product';
import { useProductStore } from '@/stores/product';
import httpService from '@/api/core/request';
import { debounce } from 'lodash-es';

export function useProductComparison() {
  const productStore = useProductStore();
  const selectedProducts = ref([{ id: '' }, { id: '' }]);
  const productOptions = ref<Product[]>([]);
  const showComparison = ref(false);
  const loadingRuleDiff = ref(false);
  const isLoading = ref(false);
  const comparisonData = ref<ProductComparison | null>(null);

  // 数据验证 schema
  const productSchema = {
    id: (value: any) => typeof value === 'string' && value.length > 0,
    name: (value: any) => typeof value === 'string' && value.length > 0,
    provider_id: (value: any) => typeof value === 'number',
    status: (value: any) => typeof value === 'number',
  };

  // 计算属性
  const basicInfoComparison = computed(() => {
    if (!comparisonData.value) return [];
    return comparisonData.value.basicInfo;
  });

  const zoneComparison = computed(() => {
    if (!comparisonData.value) return [];
    return comparisonData.value.zones;
  });

  const specialZoneComparison = computed(() => {
    if (!comparisonData.value) return [];
    return comparisonData.value.specialZones;
  });

  const rateComparison = computed(() => {
    if (!comparisonData.value) return [];
    return comparisonData.value.rates;
  });

  const isCompareDisabled = computed(() => {
    const validProducts = selectedProducts.value.filter(p => p.id).length;
    return validProducts < 2 || isLoading.value;
  });

  // 添加产品
  const handleAddProduct = () => {
    if (selectedProducts.value.length >= 4) {
      ElMessage.warning('最多只能对比 4 个产品');
      return;
    }
    selectedProducts.value.push({ id: '' });
  };

  // 移除产品
  const handleRemoveProduct = (index: number) => {
    selectedProducts.value.splice(index, 1);
    showComparison.value = false;
  };

  // 加载产品列表
  const loadProductOptions = async () => {
    isLoading.value = true;
    try {
      const products = await productStore.getProducts();
      if (Array.isArray(products) && products.length > 0) {
        productOptions.value = products;
      } else {
        throw new Error('Invalid product data');
      }
    } catch (error) {
      console.error('加载产品列表失败:', error);
      ElMessage.error('加载产品列表失败，请刷新页面重试');
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  // 开始对比 - 使用防抖
  const handleCompare = debounce(async () => {
    const productIds = selectedProducts.value.map(p => p.id).filter(id => id);

    if (productIds.length < 2) {
      ElMessage.warning('请至少选择两个产品进行对比');
      return;
    }

    loadingRuleDiff.value = true;
    isLoading.value = true;

    try {
      const comparison = await productStore.compareProducts(productIds);
      if (comparison && comparison.basicInfo && comparison.zones && 
          comparison.specialZones && comparison.rates) {
        comparisonData.value = comparison;
        showComparison.value = true;
        return comparison;
      } else {
        throw new Error('Invalid comparison data');
      }
    } catch (error) {
      console.error('对比失败:', error);
      ElMessage.error('产品对比失败，请稍后重试');
      throw error;
    } finally {
      loadingRuleDiff.value = false;
      isLoading.value = false;
    }
  }, 300);

  // 重置对比
  const resetComparison = () => {
    selectedProducts.value = [{ id: '' }, { id: '' }];
    showComparison.value = false;
    comparisonData.value = null;
  };

  return {
    selectedProducts,
    productOptions,
    showComparison,
    loadingRuleDiff,
    isLoading,
    comparisonData,
    basicInfoComparison,
    zoneComparison,
    specialZoneComparison,
    rateComparison,
    isCompareDisabled,
    handleAddProduct,
    handleRemoveProduct,
    loadProductOptions,
    handleCompare,
    resetComparison,
  };
}
