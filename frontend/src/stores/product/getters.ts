import type { Product } from '@/types/product';

export const getters = {
  getProductById: (state: any) => (id: string): Product | undefined => {
    return state.products.find((product: Product) => product.id === id);
  }
}; 