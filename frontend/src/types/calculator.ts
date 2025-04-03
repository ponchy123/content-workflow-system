import type { PaginatedResponse } from '@/api/core';
import type { TaskProgressWebSocket } from '@/api/calculator/websocket';

// 基础类型定义
export type Currency = 'USD' | 'CNY' | 'EUR';
export type WeightUnit = 'KG' | 'LB' | 'OZ';
export type DimensionUnit = 'CM' | 'IN';
export type CalculationType = 'single' | 'batch' | 'comparison';
export type CalculationStatus = 'success' | 'failed';
export type BatchCalculationStatus = 'pending' | 'processing' | 'completed' | 'failed';

// 基础费用明细接口
export interface ChargeDetail {
  name: string;
  amount: number;
  type: string;
  description?: string;
}

// 基础计算请求
export interface CalculationRequest {
  fromAddress: string;
  toAddress: string;
  weight: number;
  volume?: number;
  quantity: number;
  productType: string;
  note?: string;
  isResidential?: boolean; // 是否为住宅地址
  // 目的地详细信息
  destination_info?: {
    postal_code?: string;
    city?: string;
    state?: string;
    country?: string;
    remote_level?: string; // 偏远地区等级，与偏远地区附加费条件描述匹配
  };
}

// 计算结果详情
export interface CalculationDetails {
  weightCharge: number;
  distanceCharge: number;
  zoneCharge: number;
  volumeCharge?: number;
  additionalCharges: ChargeDetail[];
}

// 计算结果
export interface CalculationResult {
  requestId: string;
  baseCharge: number;
  fuelSurcharge: number;
  totalCharge: number;
  currency: Currency;
  details: CalculationDetails;
  error?: string;
  status?: string;
  zone?: string;
  product_code?: string; // 产品代码
  fuelRate?: number; // 燃油费率，如15表示15%
  calculationTime?: string; // 计算时间
  calculationDetails?: any[]; // 计算详情
  rawResponse?: any; // 原始API响应数据
  allSurcharges?: Array<{
    type: string;
    name: string;
    amount: number;
    condition?: string;
    reason?: string;
    condition_met?: boolean;
  }>;
  surchargeMatches?: any[]; // 附加费匹配情况
  debug?: any; // 调试信息
  peakSeasonSurcharges?: Array<{
    name?: string;
    surcharge_type?: string;
    amount?: number;
    start_date?: string;
    end_date?: string;
    condition_met?: boolean;
  }>;
}

// 历史记录
export interface CalculationHistory extends CalculationResult {
  id: string;
  timestamp: number;
  request: CalculationRequest;
}

// 历史记录详情
export interface HistoryDetail extends CalculationHistory {
  user: {
    id: number;
    username: string;
    email: string;
  };
  updatedAt: string;
}

// 查询参数
export interface HistoryListParams {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
  type?: string;
  status?: string;
  search?: string;
}

export interface HistoryListResponse extends PaginatedResponse<CalculationHistory> {}

// 批量计算
export interface BatchCalculationRequest {
  items: CalculationRequest[];
  taskName?: string;
  notifyEmail?: string;
}

export interface BatchCalculationResponse {
  taskId: string;
  status: BatchCalculationStatus;
  progress?: number;
  results?: CalculationResult[];
  error?: string;
  createdAt: string;
  updatedAt: string;
  progressWebSocket?: TaskProgressWebSocket;
  totalItems: number;
  processedItems: number;
  errorMessages: string[];
}

// 验证相关
export interface ValidationError {
  row: number;
  field: string;
  message: string;
  type?: 'error' | 'warning';
}

export interface ValidationResult {
  isValid: boolean;
  data: BatchCalculationItem[];
  errors: ValidationError[];
  warnings: ValidationError[];
}

// 批量计算项
export interface BatchCalculationItem extends CalculationRequest {
  id?: number;
  ruleId: string;
  success?: boolean;
  message?: string;
  basePrice?: number;
  fuelSurcharge?: number;
  otherFees?: number;
  totalPrice?: number;
  details?: CalculationDetails;
}

// 比较请求
export interface ComparisonRequest {
  calculationRequest: CalculationRequest;
  productTypes?: string[];
}

export interface ComparisonResult extends Omit<CalculationResult, 'requestId' | 'details'> {
  productType: string;
  recommended: boolean;
  zone?: string;
  fuelRate?: number;
}

export interface ComparisonResponse {
  results: ComparisonResult[];
}

// 批量计算任务类型
export interface BatchCalculationTask {
  task_id: string;
  file_name: string;
  original_filename?: string;
  status: BatchCalculationStatus;
  total_records: number;
  processed_records: number;
  success_records: number;
  failed_records: number;
  error_message?: string;
  result_url?: string;
  created_at: string;
  completed_at?: string;
  user_id?: string;
}
