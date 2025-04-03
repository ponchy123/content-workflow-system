import type { Product, ProductComparison } from '@/types/product';

export interface ProductState {
  products: Product[];
  loading: boolean;
  error: string | null;
}

export interface ProductGetters {
  getProductById: (id: string) => Product | undefined;
}

export interface ProductActions {
  getProducts: () => Promise<Product[]>;
  compareProducts: (productIds: string[]) => Promise<ProductComparison>;
} 