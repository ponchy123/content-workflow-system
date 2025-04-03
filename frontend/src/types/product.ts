import type { PaginatedResponse } from '@/api/core';

// 基础产品类型
export interface Product {
  id: string;
  name: string;
  code: string;
  provider: string;
  provider_name?: string;
  provider_id: number;
  description: string;
  status: boolean;
  created_at: string;
  updated_at: string;
  dim_factor: number;
  dim_factor_unit?: string;
  effective_date: string;
  expiration_date: string;
  currency: string;
  weight_unit: string;
  dim_unit: string;
  country?: string;
  enabled_weight_band?: boolean;
  enabled_start_date?: string | null;
  enabled_end_date?: string | null;
  base_fees?: any[];
  surcharges?: Array<{
    surcharge_type: string;
    sub_type?: string;
    condition_description?: string;
    amount: string;
    Zone1?: string;
    Zone2?: string;
    Zone3?: string;
    Zone4?: string;
    Zone5?: string;
    [key: string]: any;
  }>;
  seasonal_fees?: any[];
  weight_bands?: Array<{
    weight_band_id: string;
    min_weight: string;
    max_weight: string;
    unit: string;
    pricing_type: string;
    is_special: boolean;
    base_price?: string;
    Zone1: string;
    Zone2: string;
    Zone3: string;
    Zone4: string;
    Zone5: string;
    Zone6: string;
    Zone7: string;
    Zone8: string;
    Zone9?: string;
    Zone10?: string;
    Zone17: string;
    [key: string]: any;
  }>;
  base_rates?: Array<{
    weight: string;
    unit: string;
    Zone1: string;
    Zone2: string;
    Zone3: string;
    Zone4: string;
    Zone5: string;
    Zone6: string;
    Zone7: string;
    Zone8: string;
    Zone17: string;
    [key: string]: any;
  }>;
  peak_season_surcharges?: Array<{
    surcharge_type: string;
    start_date: string;
    end_date: string;
    fee_amount: string;
    [key: string]: any;
  }>;
}

// 产品CRUD请求类型
export interface ProductCreateRequest {
  name: string;
  code: string;
  provider: string;
  description?: string;
  min_weight?: number;
  max_weight?: number;
  dim_factor?: number;
  status: boolean;
  effective_date: string;
  expiration_date: string;
  currency?: string;
  min_charge?: number;
  weight_unit?: string;
  dim_unit?: string;
  fuel_surcharge_rate?: number;
}

export interface ProductUpdateRequest {
  name?: string;
  code?: string;
  provider?: string;
  description?: string;
  status?: boolean;
  dim_factor?: number;
  effective_date?: string;
  expiration_date?: string;
  currency?: string;
  weight_unit?: string;
  dim_unit?: string;
}

export interface ProductListResponse extends PaginatedResponse<Product> {}

// 添加兼容API响应格式的产品列表响应类型
export interface ApiProductListResponse {
  status: 'success' | 'error';
  code: string;
  message: string;
  data: Product[];
  timestamp: string;
  count: number;
  total?: number;
  page?: number;
  page_size?: number;
  next: string | null;
  previous: string | null;
  results: Product[];
}

// 重量相关类型
export interface WeightBand {
  id: number | string;
  product_id: string;
  weight_band_id?: string;
  min_weight: number;
  max_weight: number | null;
  pricing_type: 'STEP' | 'LINEAR';
  base_price: number;
  price_per_unit?: number;
  is_special: boolean;
  effective_date: string;
  expiration_date: string;
  status: boolean;
  weight_unit?: string;
  created_at: string;
  updated_at?: string;
}

export interface WeightRange extends WeightBand {}

export interface WeightBandCreateRequest {
  product_id?: string;
  min_weight: number;
  max_weight?: number | null;
  pricing_type: 'STEP' | 'LINEAR';
  base_price: number;
  price_per_unit?: number;
  is_special?: boolean;
  effective_date: string;
  expiration_date: string;
  status?: boolean;
}

export interface WeightRangeCreateRequest extends WeightBandCreateRequest {}

export interface WeightBandUpdateRequest {
  min_weight?: number;
  max_weight?: number | null;
  pricing_type?: 'STEP' | 'LINEAR';
  base_price?: number;
  price_per_unit?: number;
  is_special?: boolean;
  effective_date?: string;
  expiration_date?: string;
  status?: boolean;
}

export interface WeightRangeUpdateRequest extends WeightBandUpdateRequest {}

export interface WeightBandListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WeightBand[];
}

export interface WeightRangeListResponse extends WeightBandListResponse {}

// 区域费率类型
export interface ZoneRate {
  id: number | string;
  product_id: string;
  weight_band_id: string; 
  zone: string;
  base_rate: number;
  effective_date: string;
  expiration_date: string;
  status: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ZonePrice extends ZoneRate {
  weight_range_id?: string;
  price?: number;
}

export interface ZoneRateCreateRequest {
  product_id?: string;
  weight_band_id: string;
  zone: string;
  base_rate: number;
  effective_date: string;
  expiration_date: string;
  status?: boolean;
}

export interface ZonePriceCreateRequest {
  product_id?: string;
  weight_range_id: string;
  zone: string;
  price: number;
  currency?: string;
}

export interface ZoneRateUpdateRequest {
  weight_band_id?: string;
  zone?: string;
  base_rate?: number;
  effective_date?: string;
  expiration_date?: string;
  status?: boolean;
}

export interface ZonePriceUpdateRequest {
  weight_range_id?: string;
  zone?: string;
  price?: number;
  currency?: string;
}

export interface ZoneRateListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ZoneRate[];
}

export interface ZonePriceListResponse extends ZoneRateListResponse {}

// 规则类型定义
export type RuleType = 'discount' | 'surcharge' | 'threshold' | 'zone_specific' | string;
export type SurchargeType = 'fixed' | 'percentage' | 'per_kg' | 'per_shipment';

// 规则条件类型
export interface RuleCondition {
  weight_min?: number;
  weight_max?: number;
  zones?: string[];
  values?: number[];
  date_range?: {
    start: string;
    end: string;
  };
  [key: string]: any;
}

// 规则动作类型
export interface RuleAction {
  type: 'apply_discount' | 'add_fee' | 'change_rate' | string;
  value: number;
  unit?: 'percentage' | 'fixed' | string;
  [key: string]: any;
}

// 产品规则类型
export interface ProductRule {
  id: string | null;
  name: string;
  description?: string;
  rule_type: RuleType;
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  status?: boolean;
  product_id?: string;
  created_at?: string;
  updated_at?: string;
}

// 相同重量处理类型接口
export interface SameWeightHandler {
  id: string | null;
  min_weight: number;
  max_weight: number;
  weight_unit: 'KG' | 'LB';
  handling_fee: number;
  currency_code: string;
  is_active: boolean;
}

// 附加费类型接口
export interface Surcharge {
  id: string;
  product_id: string;
  name: string;
  code: string;
  surcharge_type: string;
  sub_type?: string;
  condition_description?: string;
  amount: number;
  currency_code?: string;
  effective_date: string;
  expiration_date: string;
  status: boolean;
  created_at: string;
  updated_at?: string;
  
  // 区域特定费率
  zone1_fee?: number;
  zone2_fee?: number;
  zone3_fee?: number;
  zone4_fee?: number;
  zone5_fee?: number;
  zone6_fee?: number;
  zone7_fee?: number;
  zone8_fee?: number;
  zone17_fee?: number;
  
  // 支持直接访问Zone格式的键
  [key: string]: any;
}

// 旺季附加费接口
export interface PeakSeasonSurcharge {
  id: string;
  product_id: string;
  surcharge_type: string;
  start_date: string;
  end_date: string;
  fee_amount: number;
  currency_code?: string;
  status: boolean;
  created_at: string;
  updated_at?: string;
}

// 增值服务接口
export interface ValueAddedService {
  id: string;
  product_id: string;
  service_type: string;
  name: string;
  description?: string;
  fee_amount: number;
  currency_code?: string;
  effective_date: string;
  expiration_date: string;
  status: boolean;
  created_at: string;
  updated_at?: string;
}

// 附加费类型
export const SURCHARGE_TYPES: Record<string, string> = {
  'FUEL': 'FUEL',
  'REMOTE_AREA': 'REMOTE_AREA',
  'RESIDENTIAL': 'RESIDENTIAL',
  'SIGNATURE': 'SIGNATURE',
  'INSURANCE': 'INSURANCE'
};

// 附加费类型显示名称
export const SURCHARGE_TYPE_NAMES: Record<string, string> = {
  'FUEL': '燃油附加费',
  'REMOTE_AREA': '偏远地区附加费',
  'RESIDENTIAL': '住宅地址附加费',
  'SIGNATURE': '签名服务费',
  'INSURANCE': '保险费'
};

// 旺季附加费类型
export const SEASONAL_FEE_TYPES: Record<string, string> = {
  'ADDITIONAL_HANDLING': 'ADDITIONAL_HANDLING',
  'OVERSIZE_COMMERCIAL': 'OVERSIZE',
  'OVERSIZE_RESIDENTIAL': 'RESIDENTIAL',
  'OVERWEIGHT': 'ADDITIONAL_HANDLING',
  'OVERSIZE': 'OVERSIZE_COMMERCIAL',
  'RESIDENTIAL': 'OVERSIZE_RESIDENTIAL'
};

// 旺季附加费类型显示名称
export const SEASONAL_FEE_TYPE_NAMES: Record<string, string> = {
  'ADDITIONAL_HANDLING': '附加处理费',
  'OVERSIZE_COMMERCIAL': '超大尺寸商业件',
  'OVERSIZE_RESIDENTIAL': '超大尺寸住宅件',
  'OVERWEIGHT': '附加处理费',
  'OVERSIZE': '超大尺寸商业件',
  'RESIDENTIAL': '超大尺寸住宅件'
};

// 错误响应接口
export interface ErrorResponse {
  status: 'error';
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

// 导出常量
export const WEIGHT_UNITS = ['KG', 'LB'] as const;
export const DIM_UNITS = ['CM', 'IN'] as const;
export const PRICING_TYPES = ['STEP', 'LINEAR'] as const;
export const CHARGE_TYPES = ['FIXED', 'PERCENTAGE'] as const;

// 导出类型
export type WeightUnit = typeof WEIGHT_UNITS[number];
export type DimUnit = typeof DIM_UNITS[number];
export type PricingType = typeof PRICING_TYPES[number];
export type ChargeType = typeof CHARGE_TYPES[number];

// 基础费用类型
export interface BaseFee {
  id: number | string;
  product_id: string;
  weight: number;
  weight_unit: string;
  fee_type: string;
  zone1_price?: number;
  zone2_price?: number;
  zone3_price?: number;
  zone4_price?: number;
  zone5_price?: number;
  zone6_price?: number;
  zone7_price?: number;
  zone8_price?: number;
  zone17_price?: number;
  zone1_unit_price?: number;
  zone2_unit_price?: number;
  zone3_unit_price?: number;
  zone4_unit_price?: number;
  zone5_unit_price?: number;
  zone6_unit_price?: number;
  zone7_unit_price?: number;
  zone8_unit_price?: number;
  zone17_unit_price?: number;
  effective_date?: string;
  expiration_date?: string;
  status?: boolean;
  created_at?: string;
  updated_at?: string;
}

// 修改为联合产品类型
export type ExtendedProduct = Product & {
  product_id?: string;
  product_name?: string;
  currency_code?: string;
  is_active?: boolean;
  base_rates: any[];
  weight_bands: any[];
  surcharges: any[];
  peak_season_surcharges: any[];
  zone_rates?: any[];
  special_rules?: any[];
};

/**
 * 产品版本类型定义
 */
export interface Version {
  versionId: string;
  versionName: string;
  productId: string;
  effectiveDate: string;
  expirationDate: string;
  status: 'DRAFT' | 'ACTIVE' | 'EXPIRED';
  remarks?: string;
  createdBy: string;
  createdAt: string;
  updatedAt?: string;
}

// 产品比较单元格
export interface ComparisonCell {
  valueKey: string;
  values: any[];
  differences: boolean[];
}

/**
 * 系统支持的所有区域
 * 添加新区域时，只需在此处添加即可全局生效
 */
export const SUPPORTED_ZONES = [
  'Zone1',
  'Zone2',
  'Zone3',
  'Zone4',
  'Zone5',
  'Zone6',
  'Zone7',
  'Zone8',
  'Zone17'
];

/**
 * 获取区域列表的键值对形式
 * 适用于下拉选择等场景
 */
export const ZONE_OPTIONS = SUPPORTED_ZONES.map(zone => ({
  label: zone,
  value: zone
}));

/**
 * 获取包含所有区域的默认价格对象
 * 默认值为0
 */
export function getDefaultZonePrices(): Record<string, number> {
  const prices: Record<string, number> = {};
  
  SUPPORTED_ZONES.forEach(zone => {
    const zoneKey = `zone${zone.replace('Zone', '')}`.toLowerCase();
    prices[zoneKey] = 0;
  });
  
  return prices;
}

/**
 * 获取包含所有区域的空对象
 * 用于初始化新记录
 */
export function getEmptyZoneRecord(): Record<string, any> {
  const record: Record<string, any> = {};
  
  SUPPORTED_ZONES.forEach(zone => {
    record[zone] = 0;
  });
  
  return record;
}

/**
 * 默认值配置
 */
export const DEFAULT_VALUES = {
  // 基础费率默认值
  BASE_RATES: {
    weight: 0,
    weight_unit: 'OZ',
    fee_type: 'STEP'
  },
  
  // 附加费默认值
  SURCHARGES: {
    surcharge_type: '',
    sub_type: '',
    condition_desc: ''
  },
  
  // 旺季附加费默认值
  PEAK_SEASON_SURCHARGES: {
    surcharge_type: '',
    start_date: '',
    end_date: '',
    fee_amount: 0
  }
};

/**
 * 必填字段配置
 */
export const REQUIRED_FIELDS = {
  BASE_RATES: ['weight', 'weight_unit', 'fee_type'],
  SURCHARGES: ['surcharge_type'],
  PEAK_SEASON_SURCHARGES: ['surcharge_type', 'start_date', 'end_date', 'fee_amount']
};

/**
 * 表格名称映射
 */
export const TABLE_NAME_MAP = {
  baseRates: '基础费率',
  surcharges: '附加费',
  peakSeasonSurcharges: '旺季附加费'
};

/**
 * API接口规范命名空间
 * 定义前后端数据交互的标准格式
 */
export namespace API {
  /**
   * 基础费率请求参数类型
   */
  export interface BaseFeeRequest {
    fee_id?: string | null;          // 费率ID，新增时为null
    weight: number;                  // 重量值
    weight_unit: string;             // 重量单位
    fee_type: string;                // 费率类型
    
    // 可以使用标准格式
    zone_prices?: Record<string, number>;
    
    // 也可以使用Zone格式
    Zone1?: number;
    Zone2?: number;
    Zone3?: number;
    Zone4?: number;
    Zone5?: number;
    Zone6?: number;
    Zone7?: number;
    Zone8?: number;
    Zone17?: number;
    
    // 其他可选字段
    [key: string]: any;
  }

  /**
   * 基础费率批量更新请求
   */
  export interface BaseFeeUpdateRequest {
    product_id: string;
    base_fees: BaseFeeRequest[];
  }

  /**
   * 基础费率响应类型
   */
  export interface BaseFeeResponse extends BaseFee {
    // 前端友好的Zone格式
    Zone1: number;
    Zone2: number;
    Zone3: number;
    Zone4: number;
    Zone5: number;
    Zone6: number;
    Zone7: number;
    Zone8: number;
    Zone17: number;
  }

  /**
   * 基础费率批量更新响应
   */
  export interface BaseFeeUpdateResponse {
    message: string;
    base_fees: BaseFeeResponse[];
    failed_count: number;
    failed_details: any[] | null;
    timestamp: string;
  }
}

/**
 * API接口规范文档
 * 
 * 基础费率数据传输格式规范:
 * 
 * 前端 -> 后端:
 * 1. 单个费率记录格式:
 * {
 *   "fee_id": string | null,         // 费率ID，新增时为null
 *   "weight": number,                // 重量值
 *   "weight_unit": string,           // 重量单位 (kg, lb)
 *   "fee_type": string,              // 费率类型
 *   
 *   // 标准区域价格格式 - 可以直接使用此格式，也可以使用Zone格式，两者都支持
 *   "zone_prices": {
 *     "zone1": number,               // 区域1价格
 *     "zone2": number,               // 区域2价格
 *     // ... 其他区域
 *   },
 *   
 *   // 前端也可以直接使用Zone格式发送数据，后端会自动转换
 *   "Zone1": number,                 // 区域1价格
 *   "Zone2": number,                 // 区域2价格
 *   // ... 其他区域
 *   
 *   // 可选字段
 *   "raw_data": object,              // 原始数据，保存完整格式
 *   "status": boolean,               // 状态
 * }
 * 
 * 2. 更新基础费率API:
 * POST/PUT /api/products/base_fees_by_product/?product_id=<product_id>
 * {
 *   "base_fees": [
 *     // 基础费率记录列表，格式同上
 *   ]
 * }
 * 
 * 后端 -> 前端:
 * 1. 查询响应:
 * GET /api/products/base_fees_by_product/?product_id=<product_id>
 * [
 *   {
 *     "fee_id": string,             // 费率ID
 *     "weight": number,             // 重量值
 *     "weight_unit": string,        // 重量单位
 *     "fee_type": string,           // 费率类型
 *     
 *     // 标准格式 - 可用于程序逻辑处理
 *     "zone_prices": {
 *       "zone1": number,            // 区域1价格
 *       "zone2": number,            // 区域2价格
 *       // ... 其他区域
 *     },
 *     
 *     // 前端友好格式 - 可直接用于表格显示
 *     "Zone1": number,              // 区域1价格
 *     "Zone2": number,              // 区域2价格
 *     // ... 其他区域
 *     
 *     // 可选字段
 *     "raw_data": object,           // 原始数据，完整格式
 *     "status": boolean,            // 状态
 *   }
 * ]
 * 
 * 2. 更新响应:
 * {
 *   "message": string,              // 成功消息
 *   "base_fees": [
 *     // 更新后的基础费率记录列表，格式同上
 *   ],
 *   "failed_count": number,         // 失败记录数
 *   "failed_details": array | null, // 失败详情
 *   "timestamp": string             // 时间戳
 * }
 */ 