import { get, post, del } from '@/api/core';
import type { PaginatedResponse } from '@/api/core/types';
import type { CalculationHistory, HistoryDetail } from '@/types/calculator';

export interface HistoryListParams {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
  type?: string;
  status?: string;
}

export interface HistoryListResponse extends PaginatedResponse<CalculationHistory> {}

/**
 * 获取历史记录列表
 */
export async function getHistory(page = 1, pageSize = 10): Promise<HistoryListResponse> {
  return get('/api/calculator/history', { params: { page, pageSize } });
}

/**
 * 获取历史记录详情
 */
export async function getHistoryDetail(id: string): Promise<HistoryDetail> {
  return get(`/api/calculator/history/${id}`);
}

/**
 * 删除历史记录
 */
export async function deleteHistory(): Promise<void> {
  return del('/api/calculator/history');
}

/**
 * 导出历史记录
 */
export async function exportHistory(startDate: Date, endDate: Date): Promise<Blob> {
  return get('/api/calculator/history/export', {
    params: {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
    },
    responseType: 'blob',
  });
}
