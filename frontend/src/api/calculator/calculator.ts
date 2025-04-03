import { post, get } from '@/api/core';
import type {
  CalculationRequest,
  CalculationResult,
  BatchCalculationRequest,
  BatchCalculationResponse,
  ComparisonRequest,
  ComparisonResponse,
  BatchCalculationTask
} from '@/types/calculator';
import { createTaskProgressWebSocket } from './websocket';

// API响应类型
export type ApiResponse<T> = {
  status: 'success' | 'error';
  code: string;
  message: string;
  data: T;
  timestamp: string;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

// 导出类型
export type {
  CalculationRequest,
  CalculationResult,
  BatchCalculationRequest,
  BatchCalculationResponse,
  ComparisonRequest,
  ComparisonResponse,
  BatchCalculationTask,
};

// 单条运费计算
export const calculate = async (data: CalculationRequest): Promise<CalculationResult> => {
  try {
    console.log("计算请求数据:", data);
    const response = await post<CalculationResult>('/api/v1/calculator/calculate/', data);
    console.log("计算响应完整数据:", response);
    return response.data;
  } catch (error) {
    console.error("计算请求错误:", error);
    throw error;
  }
};

// 批量运费计算
export async function calculateBatch(
  request: BatchCalculationRequest
): Promise<BatchCalculationResponse> {
  const { data: response } = await post<BatchCalculationResponse>('/api/v1/calculator/batch', request);

  // 创建WebSocket连接以监听任务进度
  if (response.taskId) {
    createTaskProgressWebSocket(response.taskId);
  }

  return response;
}

// 获取批量任务状态
export async function getBatchTaskStatus(taskId: string): Promise<BatchCalculationTask> {
  const { data: response } = await get<BatchCalculationTask>(`/api/v1/calculator/batch/${taskId}`);
  return response;
}

// 取消批量任务
export async function cancelBatchTask(taskId: string): Promise<void> {
  await post(`/api/v1/calculator/batch/${taskId}/cancel`);
}

// 重试失败的条目
export async function retryFailedItems(
  taskId: string,
  itemIds: string[]
): Promise<BatchCalculationResponse> {
  const { data: response } = await post<BatchCalculationResponse>(
    `/api/v1/calculator/batch/${taskId}/retry`,
    { item_ids: itemIds }
  );

  return response;
}

// 产品费率比较
export const compareProducts = async (data: ComparisonRequest): Promise<ComparisonResponse> => {
  const { data: response } = await post<ComparisonResponse>('/api/v1/calculator/compare', data);
  return response;
};

// 保存计算结果
export const saveCalculationResult = async (data: CalculationResult): Promise<void> => {
  await post('/api/v1/calculator/save', data);
};
