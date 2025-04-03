import { get, post, put, del } from '../core';
import type { PaginatedResponse } from '../core/types';
import type {
  FuelRate,
  FuelRateCreateRequest,
  FuelRateUpdateRequest,
  FuelRateHistory,
  FuelRateHistoryListResponse,
  FuelRateTrendData,
  ProviderType,
} from '@/types/fuelRate';
import request from '@/api/core/request';

export type {
  FuelRate,
  FuelRateCreateRequest,
  FuelRateUpdateRequest,
  FuelRateHistory,
  FuelRateHistoryListResponse,
  FuelRateTrendData,
  ProviderType,
};

// 燃油费率管理API
export const getFuelRates = async (params?: {
  page?: number;
  page_size?: number;
  provider_id?: number;
  current_only?: boolean;
  status?: boolean;
}): Promise<FuelRate[]> => {
  const { data } = await get<FuelRate[]>('/api/v1/fuel-rates/rates/', { params });
  return data;
};

export const getFuelRate = async (rateId: string): Promise<FuelRate> => {
  const { data } = await get<FuelRate>(`/api/v1/fuel-rates/rates/${rateId}/`);
  return data;
};

export const createFuelRate = async (data: FuelRateCreateRequest): Promise<FuelRate> => {
  const { data: response } = await post<FuelRate>('/api/v1/fuel-rates/rates/', data);
  return response;
};

export const updateFuelRate = async (
  rateId: string,
  data: FuelRateUpdateRequest,
): Promise<FuelRate> => {
  const { data: response } = await put<FuelRate>(`/api/v1/fuel-rates/rates/${rateId}/`, data);
  return response;
};

export function toggleFuelRateStatus(id: string) {
  return request({
    url: `/api/v1/fuel-rates/rates/${id}/toggle_status/`,
    method: 'post'
  });
}

export function deleteFuelRate(id: string) {
  return request({
    url: `/api/v1/fuel-rates/rates/${id}/`,
    method: 'delete'
  });
}

export const getCurrentFuelRates = async (providerId?: number): Promise<FuelRate[]> => {
  const params = providerId ? { provider_id: providerId } : undefined;
  const { data } = await get<FuelRate[]>('/api/v1/fuel-rates/rates/current/', { params });
  return data;
};

// 燃油费率历史记录
export const getFuelRateHistory = async (params?: {
  page?: number;
  page_size?: number;
  rate_id?: string;
  operator?: number;
  change_type?: string;
}): Promise<FuelRateHistoryListResponse> => {
  const { data } = await get<FuelRateHistoryListResponse>('/api/v1/fuel-rates/histories/', { params });
  return data;
};

// 燃油费率趋势
export const getFuelRateTrend = async (
  provider: ProviderType,
  startDate: string,
  endDate: string,
): Promise<FuelRateTrendData> => {
  const { data } = await get<FuelRateTrendData>('/api/v1/fuel-rates/rates/trend/', {
    params: {
      provider,
      start_date: startDate,
      end_date: endDate,
    },
  });
  return data;
};
