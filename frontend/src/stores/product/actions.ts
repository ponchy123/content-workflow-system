import httpService from '@/api/core/request';
import type { Product, ProductComparison } from '@/types/product';

export const actions = {
  // 获取产品列表
  getProducts: async function(this: any): Promise<Product[]> {
    this.loading = true;
    this.error = null;
    try {
      const response = await httpService.get('/api/products');
      this.products = response.data;
      return this.products;
    } catch (err) {
      this.error = '获取产品列表失败';
      throw err;
    } finally {
      this.loading = false;
    }
  },

  // 对比产品
  compareProducts: async function(this: any, productIds: string[]): Promise<ProductComparison> {
    this.loading = true;
    this.error = null;
    try {
      const response = await httpService.post('/api/products/compare', { productIds });
      return response.data;
    } catch (err) {
      this.error = '产品对比失败';
      throw err;
    } finally {
      this.loading = false;
    }
  }
}; 