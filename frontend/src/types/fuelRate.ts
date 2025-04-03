// 燃油费率类型定义
export interface FuelRate {
  rate_id: number;
  provider: number;
  provider_name: string;
  rate_value: number;
  effective_date: string;
  expiration_date: string;
  status: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

// 燃油费率表单类型
export interface FuelRateForm {
  provider: number;
  rate_value: number;
  effective_date: string;
  expiration_date: string;
  description?: string;
  status: boolean;
}

// 燃油费率创建请求
export interface FuelRateCreateRequest {
  provider: number;
  rate_value: number;
  effective_date: string;
  expiration_date: string;
  description?: string;
  status: boolean;
}

// 燃油费率更新请求
export interface FuelRateUpdateRequest {
  provider?: number;
  rate_value?: number;
  effective_date?: string;
  expiration_date?: string;
  description?: string;
  status?: boolean;
}

// 燃油费率历史记录
export interface FuelRateHistory {
  id: number;
  fuel_rate_id: number;
  old_rate: number;
  new_rate: number;
  change_type: string;
  change_reason?: string;
  change_time: string;
  operator_id?: number;
  operator_name?: string;
}

// 燃油费率查询参数
export interface FuelRateQueryParams {
  provider_id?: number;
  status?: boolean;
  effective_date_after?: string;
  effective_date_before?: string;
  page?: number;
  page_size?: number;
  dateRange?: string[];
}

// 服务商类型
export interface ProviderType {
  id: number;
  name: string;
  code: string;
  status: boolean;
}

export interface FuelRateListResponse {
  items: FuelRate[];
  total: number;
  page: number;
  page_size: number;
}

export interface FuelRateHistoryListResponse {
  items: FuelRateHistory[];
  total: number;
  page: number;
  page_size: number;
}

// 定义趋势图数据结构，增强类型安全性
export interface FuelRateTrendPoint {
  date: string;
  rate: number;
}

export interface FuelRateTrendData {
  provider: ProviderType;
  data: FuelRateTrendPoint[];
}
