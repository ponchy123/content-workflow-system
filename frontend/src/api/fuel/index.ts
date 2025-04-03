// 导出燃油费率管理相关的API函数
export {
  getFuelRates,
  getFuelRate,
  createFuelRate,
  updateFuelRate,
  deleteFuelRate,
  getFuelRateHistory,
  getFuelRateTrend,
} from './fuelRates';

// 导出类型定义
export type {
  FuelRate,
  FuelRateCreateRequest,
  FuelRateUpdateRequest,
  FuelRateHistory,
  FuelRateHistoryListResponse,
  FuelRateTrendData,
  ProviderType,
} from './fuelRates';
