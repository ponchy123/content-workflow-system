import { get, post } from '@/api/core';
import type {
  CalculationRequest,
  CalculationResult,
  BatchCalculationRequest,
  BatchCalculationResponse,
  HistoryListParams,
  HistoryListResponse,
  ValidationResult
} from '@/types/calculator';
import type { ApiResponse } from '@/types/common';
import { isRemoteLevelMatch } from '@/utils/postal';
import request from '@/api/core/request';
import type { AxiosResponse } from 'axios';
import axios from 'axios';
import { TOKEN_KEY } from '@/types/auth';
import { useUserStore } from '@/stores/user';

// 计算运费
export async function calculateFreight(data: any): Promise<CalculationResult> {
  console.log('运费计算请求数据:', JSON.stringify(data));
  try {
    // 从localStorage获取正确的token
    const userToken = localStorage.getItem(TOKEN_KEY);
    
    if (!userToken || userToken === 'null' || userToken === 'undefined') {
      console.error('计算运费失败: 用户未登录或token无效');
      
      // 尝试获取用户存储并刷新token
      try {
        const userStore = useUserStore();
        if (userStore && userStore.refreshTokenHandler) {
          console.log('尝试刷新token...');
          await userStore.refreshTokenHandler();
          console.log('token刷新成功，继续计算运费');
          return calculateFreight(data); // 递归调用，使用刷新后的token
        }
      } catch (refreshError) {
        console.error('刷新token失败:', refreshError);
        throw new Error('认证失败：请重新登录系统');
      }
      
      throw new Error('认证失败：请先登录系统');
    }
    
    console.log('使用的认证token (部分):', userToken.substring(0, 10) + '...');
    
    // 确保请求参数包含所有必要的附加费相关字段
    const requestData = {
      ...data,
      // 添加product_id字段，保留原有的productType用于前端显示
      product_id: data.productType,
      include_all_surcharges: true,  // 要求返回所有附加费，包括不满足条件的
      return_calculation_details: true,  // 返回计算细节
      verbose: true,  // 更详细的返回结果
      return_debug_info: true,  // 要求返回调试信息
      return_surcharge_matches: true,  // 要求返回附加费匹配情况
      show_calculation_process: true,  // 显示完整计算过程
    };
    
    console.log('增强后的运费计算请求数据:', JSON.stringify(requestData, null, 2));
    
    // 使用直接的axios实例，但正确添加token
    const response = await axios({
      method: 'post',
      url: '/api/v1/calculator/calculate/',
      baseURL: import.meta.env.VITE_API_BASE_URL || '',
      data: requestData,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}`,
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache, no-store, must-revalidate', // 确保每次请求都从服务器获取最新数据
        'Pragma': 'no-cache'
      }
    });
    
    // 直接打印整个响应对象查看结构
    console.log('运费计算完整响应状态:', response.status, response.statusText);
    console.log('运费计算完整响应头:', response.headers);
    console.log('运费计算完整响应数据:', JSON.stringify(response.data, null, 2));
    
    // 检查响应数据
    if (!response || !response.data) {
      throw new Error('API响应数据为空');
    }
    
    // 获取响应数据
    const responseData = response.data;
    console.log('运费计算响应数据类型:', typeof responseData);
    
    // 解析附加费信息
    const allSurcharges = responseData.all_surcharges || responseData.surcharges || [];
    const peakSeasonSurcharges = responseData.peak_season_surcharges || [];
    
    // 打印附加费信息
    console.log('所有附加费数量:', allSurcharges.length);
    if (allSurcharges.length > 0) {
      console.log('附加费明细:', JSON.stringify(allSurcharges, null, 2));
    }
    
    console.log('旺季附加费数量:', peakSeasonSurcharges.length);
    if (peakSeasonSurcharges.length > 0) {
      console.log('旺季附加费明细:', JSON.stringify(peakSeasonSurcharges, null, 2));
    }
    
    // 组装结果对象
    const result: CalculationResult = {
      requestId: responseData.request_id || '',
      baseCharge: typeof responseData.base_fee === 'number' ? responseData.base_fee : 
                 ((responseData.calculation_details && responseData.calculation_details.length > 0) ? 
                  Number(responseData.calculation_details[0]?.amount || 0) : Number(responseData.base_fee) || 0),
      fuelSurcharge: typeof responseData.fuel_surcharge === 'number' ? responseData.fuel_surcharge : Number(responseData.fuel_surcharge) || 0,
      totalCharge: typeof responseData.total_fee === 'number' ? responseData.total_fee : Number(responseData.total_fee) || 0,
      currency: responseData.currency || 'USD',
      zone: responseData.zone || '',
      fuelRate: responseData.fuel_rate ? Number(responseData.fuel_rate) : 15,
      details: {
        weightCharge: typeof responseData.weight_charge === 'number' ? responseData.weight_charge : Number(responseData.weight_charge) || 0,
        distanceCharge: typeof responseData.distance_charge === 'number' ? responseData.distance_charge : Number(responseData.distance_charge) || 0,
        zoneCharge: typeof responseData.zone_charge === 'number' ? responseData.zone_charge : Number(responseData.zone_charge) || 0,
        volumeCharge: typeof responseData.volume_charge === 'number' ? responseData.volume_charge : Number(responseData.volume_charge) || 0,
        additionalCharges: allSurcharges
      },
      // 保存原始响应以便调试
      rawResponse: responseData,
      // 保留原始字段，确保可以在UI中显示
      allSurcharges: allSurcharges,
      surchargeMatches: responseData.surcharge_matches || [],
      calculationDetails: responseData.calculation_details || [],
      debug: responseData.debug_info || {},
      peakSeasonSurcharges: peakSeasonSurcharges
    };
    
    console.log('运费计算结果处理后:', JSON.stringify(result, null, 2));
    return result;
  } catch (error: any) {
    console.error('运费计算失败:', error);
    
    // 处理401错误
    if (error.response && error.response.status === 401) {
      console.error('认证失败：', error.response.data);
      // 尝试刷新token
      try {
        const userStore = useUserStore();
        if (userStore && userStore.refreshTokenHandler) {
          await userStore.refreshTokenHandler();
          return calculateFreight(data); // 递归调用，使用刷新后的token
        }
      } catch (refreshError) {
        console.error('刷新token失败:', refreshError);
        throw new Error('认证失败：请重新登录系统');
      }
    }
    
    // 如果有响应但状态码不是200
    if (error.response) {
      console.error('API错误响应:', error.response.status, error.response.statusText);
      console.error('API错误数据:', error.response.data);
    }
    
    // 处理其他错误
    throw error;
  }
}

// 获取产品类型列表
export const getProductTypes = async () => {
  try {
    // 从localStorage获取token
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    
    // 使用get方法获取产品类型数据
    const response = await get<ApiResponse<any[]>>('/api/v1/products/product-types/', {
      headers: token ? {
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache',
      } : undefined
    });
    
    // 返回数据
    if (response && Array.isArray(response)) {
      console.log('成功获取产品类型数据:', response);
      return response;
    } else if (response && response.data && Array.isArray(response.data)) {
      console.log('成功获取产品类型数据(data属性):', response.data);
      return response.data;
    } else {
      console.warn('产品类型API返回格式不符合预期:', response);
      return generateMockProductData();
    }
  } catch (error) {
    console.error('获取产品类型出错，使用模拟数据:', error);
    return generateMockProductData();
  }
};

// 模拟产品数据生成函数
const generateMockProductData = () => {
  console.log('生成模拟产品数据');
  return [
    { 
      product_id: "FEDEX_GROUND", 
      product_name: "联邦快递陆运", 
      provider_name: "FedEx",
      currency: "USD",
      status: true,
      dim_unit: "in",
      weight_unit: "lb",
      dim_factor: "166",
      dim_factor_unit: "in³/lb"
    },
    {
      product_id: "FEDEX_EXPRESS", 
      product_name: "联邦快递特快", 
      provider_name: "FedEx",
      currency: "USD",
      status: true,
      dim_unit: "in",
      weight_unit: "lb",
      dim_factor: "166",
      dim_factor_unit: "in³/lb"
    },
    {
      product_id: "UPS_GROUND", 
      product_name: "UPS 陆运", 
      provider_name: "UPS",
      currency: "USD",
      status: true,
      dim_unit: "in",
      weight_unit: "lb",
      dim_factor: "166",
      dim_factor_unit: "in³/lb"
    }
  ];
};

// 获取服务等级列表
export const getServiceLevels = async () => {
  const response = await get<ApiResponse<any[]>>('/api/v1/products/service-levels/');
  return response.data;
};

// 批量计算运费
export const calculateBatch = (
  data: BatchCalculationRequest,
): Promise<BatchCalculationResponse> => {
  return post('/api/v1/calculator/batch/', data);
};

// 获取批量计算任务状态
export const getBatchTaskStatus = (taskId: string): Promise<BatchCalculationResponse> => {
  return get(`/api/v1/calculator/batch/${taskId}/status/`);
};

// 取消批量计算任务
export const cancelBatchTask = (taskId: string): Promise<void> => {
  return post(`/api/v1/calculator/batch/${taskId}/cancel/`);
};

// 获取历史记录列表
export const getHistory = (params: HistoryListParams): Promise<HistoryListResponse> => {
  return get('/api/v1/calculator/history/', { params });
};

// 导出历史记录
export const exportHistory = (params: HistoryListParams): Promise<Blob> => {
  return get('/api/v1/calculator/history/export/', {
    ...params,
    responseType: 'blob',
  });
};

// 保存计算结果
export const saveCalculationResult = (data: CalculationRequest): Promise<void> => {
  return post('/api/v1/calculator/save/', data);
};

// 计算费用 (v1 版本)
export const calculateFee = (data: CalculationRequest): Promise<CalculationResult> => {
  // 如果存在偏远地区信息，添加日志，便于调试匹配逻辑
  if (data.destination_info?.remote_level) {
    console.log(`计算运费 - 偏远地区等级: ${data.destination_info.remote_level}`);
    // 添加日志，后端将尝试匹配哪些附加费
    console.log(`偏远地区附加费匹配将根据条件描述与偏远等级进行精确匹配`);
  }
  
  return post('/v1/calculator/calculate/', data);
};

// 批量计算费用 (v1 版本)
export const batchCalculate = (
  data: BatchCalculationRequest,
): Promise<BatchCalculationResponse> => {
  return post('/v1/calculator/batch/', data);
};

// 获取历史记录详情
export const getHistoryDetail = (id: string): Promise<any> => {
  return get(`/api/v1/calculator/history/${id}/`);
};

// 获取产品类型列表（异步版本）
export const getProductTypesAsync = async () => {
  return getProductTypes();
};

// 获取服务等级列表（异步版本）
export const getServiceLevelsAsync = async () => {
  return getServiceLevels();
};

// 比较产品
export const compareProductsAsync = async (data: any) => {
  return post('/api/v1/calculator/compare/', data);
};

// 下载模板
export const downloadTemplate = (): Promise<Blob> => {
  return get('/api/v1/calculator/template/', { responseType: 'blob' });
};

// 验证数据
export const validateData = (file: File): Promise<ValidationResult> => {
  const formData = new FormData();
  formData.append('file', file);
  return post('/api/v1/calculator/validate/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 辅助函数：匹配偏远地区附加费
export function matchRemoteAreaSurcharge(surcharges: any[], remoteLevel: string): any | null {
  if (!surcharges || !surcharges.length || !remoteLevel) return null;
  
  // 筛选出偏远地区附加费
  const remoteSurcharges = surcharges.filter(
    s => s.surcharge_type === 'DELIVERY_AREA_SURCHARGE' || 
         s.name?.includes('偏远地区') || 
         s.name?.includes('DAS Remote')
  );
  
  if (!remoteSurcharges.length) return null;
  
  // 首先尝试完全匹配
  let matchedSurcharge = remoteSurcharges.find(
    s => s.condition_description === remoteLevel
  );
  
  // 如果没有完全匹配，尝试使用辅助函数匹配
  if (!matchedSurcharge) {
    matchedSurcharge = remoteSurcharges.find(
      s => isRemoteLevelMatch(remoteLevel, s.condition_description)
    );
  }
  
  return matchedSurcharge;
}

/**
 * 获取产品列表
 */
export function getProducts(): Promise<AxiosResponse<any>> {
  return request({
    url: '/api/v1/products/',
    method: 'get'
  });
}
