/**
 * API响应的基础接口
 */
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  code: string;
  message: string;
  data: T;
  timestamp: string;
}

/**
 * 分页响应的基础接口
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 分页请求的基础接口
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
}

/**
 * API错误响应的接口
 */
export interface ApiError {
  status: 'error';
  code: string;
  message: string;
  data: null;
  timestamp: string;
  errors?: Record<string, string[]>;
}

/**
 * 基础实体接口
 */
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

/**
 * 排序参数接口
 */
export interface SortParams {
  sort_by?: string;
  order?: 'asc' | 'desc';
}

/**
 * 文件上传响应接口
 */
export interface UploadResponse {
  url: string;
  filename: string;
  size: number;
  mime_type: string;
}

/**
 * 自定义错误代码枚举
 */
export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  PRODUCT_NOT_FOUND = 'PRODUCT_NOT_FOUND',
  WEIGHT_RANGE_NOT_FOUND = 'WEIGHT_RANGE_NOT_FOUND',
  ZONE_PRICE_NOT_FOUND = 'ZONE_PRICE_NOT_FOUND',
  INVALID_PARAMETER = 'INVALID_PARAMETER',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  CALCULATION_ERROR = 'CALCULATION_ERROR',
  BATCH_PROCESSING_ERROR = 'BATCH_PROCESSING_ERROR',
  CALCULATION_TIMEOUT = 'CALCULATION_TIMEOUT',
  RESOURCE_LIMIT_EXCEEDED = 'RESOURCE_LIMIT_EXCEEDED',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
}

export interface SecurityConfig {
  CSRF_HEADER: string;
  CSRF_COOKIE: string;
  ENCRYPTION_KEY: string;
  SENSITIVE_FIELDS: string[];
}
