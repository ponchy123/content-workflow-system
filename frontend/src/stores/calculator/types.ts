import type { Product } from '@/types/product';

export interface Package {
  length: number;
  width: number;
  height: number;
  weight: number;
  quantity: number;
  declaredValue?: number;
}

export interface CalcResult {
  productId: string;
  productName: string;
  baseCharge: number;
  surcharges: Surcharge[];
  totalCharge: number;
  calculationTime?: string;
  details: {
    zone: string;
    dimWeight: number;
    chargeWeight: number;
    ratePerWeight: number;
    [key: string]: any;
  };
}

export interface Surcharge {
  name: string;
  description?: string;
  amount: number;
  type: 'FIXED' | 'PERCENT';
  isAdditional: boolean;
  [key: string]: any;
}

export interface ComparisonResult {
  baseResults: CalcResult[];
  comparisonTable: any[];
}

export interface CalcParams {
  productIds: string[];
  originZip: string;
  destZip: string;
  packages: Package[];
  options?: {
    signatureRequired?: boolean;
    insurance?: boolean;
    saturdayDelivery?: boolean;
    residentialDelivery?: boolean;
    [key: string]: any;
  };
}

export interface BatchCalcParams {
  file: File;
  productIds: string[];
  options?: Record<string, any>;
}

export interface BatchCalcResult {
  taskId: string;
  processedCount: number;
  totalCount: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  results?: CalcResult[];
  errors?: Record<string, string>;
}

export interface CalculatorState {
  products: Product[];
  selectedProductIds: string[];
  calcParams: CalcParams;
  calcResults: CalcResult[];
  comparisonResult: ComparisonResult | null;
  batchCalcResult: BatchCalcResult | null;
  recentSearches: CalcParams[];
  loading: boolean;
  error: string | null;
}

export interface CalculatorGetters {
  availableProducts: Product[];
  selectedProducts: Product[];
  totalPackages: number;
  totalWeight: number;
  totalChargeWeight: number;
  bestProductResult: CalcResult | null;
}

export interface CalculatorActions {
  calculateSingle: (params: CalcParams) => Promise<CalcResult[]>;
  compareProducts: (params: CalcParams) => Promise<ComparisonResult>;
  calculateBatch: (params: BatchCalcParams) => Promise<BatchCalcResult>;
  getTaskStatus: (taskId: string) => Promise<BatchCalcResult>;
  loadProducts: () => Promise<Product[]>;
  selectProduct: (productId: string) => void;
  deselectProduct: (productId: string) => void;
  toggleProductSelection: (productId: string) => void;
  resetCalculator: () => void;
  addPackage: (pkg: Package) => void;
  updatePackage: (index: number, pkg: Package) => void;
  removePackage: (index: number) => void;
  clearPackages: () => void;
  saveSearch: (params: CalcParams) => void;
} 