/**
 * 错误处理工具
 */

import { ElMessage } from 'element-plus';

// 错误类型定义
export enum ErrorType {
  NETWORK = 'NETWORK',
  API = 'API',
  VALIDATION = 'VALIDATION',
  AUTH = 'AUTH',
  BUSINESS = 'BUSINESS',
  PRODUCT = 'PRODUCT',
  DATA_FORMAT = 'DATA_FORMAT',
  UNKNOWN = 'UNKNOWN',
}

// 错误码定义
export enum ErrorCode {
  NETWORK_ERROR = 'NETWORK_ERROR',
  API_ERROR = 'API_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  BUSINESS_ERROR = 'BUSINESS_ERROR',
  PRODUCT_ERROR = 'PRODUCT_ERROR',
  DATA_FORMAT_ERROR = 'DATA_FORMAT_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

// 自定义错误类
export class AppError extends Error {
  constructor(
    message: string,
    public type: ErrorType = ErrorType.UNKNOWN,
    public code: string = ErrorCode.UNKNOWN_ERROR,
    public details?: Record<string, any>,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// 网络错误
export class NetworkError extends AppError {
  constructor(message: string = '网络请求失败', details?: Record<string, any>) {
    super(message, ErrorType.NETWORK, ErrorCode.NETWORK_ERROR, details);
    this.name = 'NetworkError';
  }
}

// API错误
export class ApiError extends AppError {
  constructor(
    message: string,
    public status: number,
    details?: Record<string, any>,
  ) {
    super(message, ErrorType.API, ErrorCode.API_ERROR, details);
    this.name = 'ApiError';
  }
}

// 验证错误
export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, ErrorType.VALIDATION, ErrorCode.VALIDATION_ERROR, details);
    this.name = 'ValidationError';
  }
}

// 认证错误
export class AuthError extends AppError {
  constructor(message: string = '认证失败', details?: Record<string, any>) {
    super(message, ErrorType.AUTH, ErrorCode.AUTH_ERROR, details);
    this.name = 'AuthError';
  }
}

// 业务错误
export class BusinessError extends AppError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, ErrorType.BUSINESS, ErrorCode.BUSINESS_ERROR, details);
    this.name = 'BusinessError';
  }
}

// 产品错误
export class ProductError extends AppError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, ErrorType.PRODUCT, ErrorCode.PRODUCT_ERROR, details);
    this.name = 'ProductError';
  }
}

// 数据格式错误
export class DataFormatError extends AppError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, ErrorType.DATA_FORMAT, ErrorCode.DATA_FORMAT_ERROR, details);
    this.name = 'DataFormatError';
  }
}

// 错误处理函数
export function handleError(error: unknown): void {
  console.error('Error:', error);

  if (error instanceof AppError) {
    // 处理应用级错误
    switch (error.type) {
      case ErrorType.NETWORK:
        ElMessage.error('网络连接失败，请检查网络设置');
        break;
      case ErrorType.API:
        ElMessage.error(`API请求失败: ${error.message}`);
        break;
      case ErrorType.VALIDATION:
        ElMessage.warning(error.message);
        break;
      case ErrorType.AUTH:
        ElMessage.error(error.message);
        // 可以在这里处理登录跳转
        break;
      case ErrorType.BUSINESS:
        ElMessage.warning(error.message);
        break;
      case ErrorType.PRODUCT:
        ElMessage.error(`产品错误: ${error.message}`);
        break;
      case ErrorType.DATA_FORMAT:
        ElMessage.warning(`数据格式错误: ${error.message}`);
        break;
      default:
        ElMessage.error('发生未知错误');
    }
  } else if (error instanceof Error) {
    // 处理标准 Error
    ElMessage.error(error.message);
  } else {
    // 处理其他类型错误
    ElMessage.error('发生未知错误');
  }
}

// 错误日志记录
export function logError(error: unknown): void {
  if (error instanceof AppError) {
    console.error(`[${error.type}] ${error.name}: ${error.message}`, error.details);
  } else {
    console.error('Unhandled Error:', error);
  }

  // 这里可以添加错误上报逻辑
  // reportError(error);
}

// 统一的错误处理函数
export async function withErrorHandler<T>(
  fn: () => Promise<T>,
  customHandler?: (error: unknown) => void,
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (error) {
    if (customHandler) {
      customHandler(error);
    } else {
      handleError(error);
    }
    logError(error);
    return undefined;
  }
}

/**
 * 处理产品验证错误
 * @param errors 错误信息数组
 */
export function handleProductValidationErrors(errors: string[]): void {
  if (errors.length === 0) return;
  
  const errorMessage = errors.join('\n');
  const validationError = new ValidationError(errorMessage, { errors });
  handleError(validationError);
}

/**
 * 处理API响应错误
 * @param response API响应
 */
export function handleApiResponseError(response: any): void {
  let errorMessage = '请求失败';
  let errorDetails: Record<string, any> = {};
  
  if (response && typeof response === 'object') {
    if (response.message) {
      errorMessage = response.message;
    }
    
    if (response.errors) {
      errorDetails.errors = response.errors;
    }
    
    if (response.status) {
      errorDetails.status = response.status;
    }
  }
  
  const apiError = new ApiError(errorMessage, errorDetails.status || 500, errorDetails);
  handleError(apiError);
}

/**
 * 处理产品数据错误
 * @param message 错误消息
 * @param details 错误详情
 */
export function handleProductError(message: string, details?: Record<string, any>): void {
  const productError = new ProductError(message, details);
  handleError(productError);
}

/**
 * 处理数据格式错误
 * @param message 错误消息
 * @param details 错误详情
 */
export function handleDataFormatError(message: string, details?: Record<string, any>): void {
  const dataFormatError = new DataFormatError(message, details);
  handleError(dataFormatError);
}
