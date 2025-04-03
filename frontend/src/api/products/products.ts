import { get, post, put, del } from '@/api/core/request';
import endpoints from './endpoints';
import type {
  Product,
  ProductCreateRequest,
  ProductUpdateRequest,
  ProductListResponse,
  ApiProductListResponse,
  WeightRange,
  WeightBand,
  ZoneRate,
  Surcharge,
  PeakSeasonSurcharge,
  ProductRule as SpecialRule,
  ErrorResponse
} from '@/types/product';
import { axiosInstance } from '../core/request';

// 产品管理API
const productAPI = {
  list: '/api/v1/products/',
  detail: (id: string) => `/api/v1/products/${id}/`,
  create: '/api/v1/products/',
  update: (id: string) => `/api/v1/products/${id}/`,
  delete: (id: string) => `/api/v1/products/${id}/`,
};

export async function getProducts(queryParams: {
  page?: number;
  pageSize?: number;
  search?: string;
  provider?: string;
  isActive?: boolean;
  show_all?: boolean;
  t?: number;
}): Promise<ApiProductListResponse | ProductListResponse | ErrorResponse> {
  try {
    console.log('开始请求产品列表，参数:', queryParams);
    
    // 添加当前时间戳防止缓存
    const timestamp = new Date().getTime();
    const params = { 
      ...queryParams,
      // 转换参数名称以匹配后端API预期
      page_size: queryParams.pageSize,
      t: timestamp // 添加时间戳
    };
    
    console.log('请求参数:', params);
    const response = await get(productAPI.list, { params }) as any;
    console.log('API响应:', response);
    
    return response;
  } catch (error) {
    console.error('获取产品列表失败:', error);
    throw error;
  }
}

/**
 * 处理产品数据字段映射，确保前后端字段一致
 * 
 * @param productData 原始产品数据
 * @returns 规范化后的产品数据
 */
function normalizeProductData(productData: any): any {
  if (!productData) return productData;
  
  const normalizedData = { ...productData };
  
  // 处理字段映射
  if ('product_name' in normalizedData) {
    normalizedData.name = normalizedData.product_name;
    delete normalizedData.product_name;
  }
  
  if ('currency_code' in normalizedData) {
    normalizedData.currency = normalizedData.currency_code;
    delete normalizedData.currency_code;
  }
  
  // 处理状态字段
  if ('is_active' in normalizedData) {
    normalizedData.status = normalizedData.is_active;
    delete normalizedData.is_active;
  }
  
  // 数字状态转换为布尔值
  if ('status' in normalizedData && typeof normalizedData.status === 'number') {
    normalizedData.status = Boolean(normalizedData.status === 1);
  }
  
  // 处理重量段相关字段
  if ('weight_ranges' in normalizedData) {
    normalizedData.weight_bands = normalizedData.weight_ranges;
    delete normalizedData.weight_ranges;
  }
  
  if ('enabled_weight_range' in normalizedData) {
    normalizedData.enabled_weight_band = normalizedData.enabled_weight_range;
    delete normalizedData.enabled_weight_range;
  }
  
  return normalizedData;
}

// 添加和导出更详细的错误响应接口
interface ProductApiErrorResponse {
  error: boolean;
  message: string;
  status?: string;
  code?: string;
  data?: any;
}

// 使用已导入的ErrorResponse类型或使用本地定义的类型
export type { ErrorResponse };

// 获取单个产品详情
export async function getProduct(id: string) {
  try {
    console.log('获取产品详情，ID:', id);
    const response = await get(productAPI.detail(id));
    console.log('获取产品详情响应:', response);
    return response;
  } catch (error) {
    console.error('获取产品详情失败:', error);
    throw error;
  }
}

export async function createProduct(data: ProductCreateRequest): Promise<Product | ErrorResponse> {
  try {
    console.log('创建产品，数据:', data);
    const response = await post(productAPI.create, data);
    console.log('创建产品响应:', response);
    return response.data as Product;
  } catch (error) {
    console.error('创建产品失败:', error);
    throw error;
  }
}

export async function updateProduct(id: string, data: ProductUpdateRequest): Promise<Product | ErrorResponse> {
  try {
    console.log('更新产品，ID:', id, '数据:', data);
    const response = await put(productAPI.update(id), data);
    console.log('更新产品响应:', response);
    return response.data as Product;
  } catch (error) {
    console.error('更新产品失败:', error);
    throw error;
  }
}

export async function deleteProduct(id: string | number): Promise<any> {
  try {
    console.log('删除产品，ID:', id);
    const response = await del(productAPI.delete(String(id)));
    console.log('删除产品响应:', response);
    return response;
  } catch (error) {
    console.error('删除产品失败:', error);
    throw error;
  }
}

// 获取重量范围
export async function getWeightRanges(productId: string): Promise<WeightBand[] | ErrorResponse> {
  try {
    console.log(`获取重量范围，产品ID:`, productId);
    const response = await get('/api/v1/products/base-fees/', { params: { product_id: productId } });
    
    // 处理空数据情况
    if (response?.data) {
      // 将BaseFee数据转换为WeightBand格式以保持向后兼容
      const weightBands = Array.isArray(response.data) ? response.data.map((item: any) => {
        return {
          id: item.fee_id || item.id,
          product_id: item.product,
          weight: item.weight,
          weight_unit: item.weight_unit,
          pricing_type: item.fee_type,
          weight_band_id: `BF${item.fee_id || item.id}`,
          is_special: false,
          status: true,
          // 保留其他字段
          ...item
        };
      }) : [];
      
      return weightBands;
    }
    
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取重量范围失败:', error);
    return []; // 错误时返回空数组
  }
}

// 获取区域价格
export async function getZonePrices(productId: string): Promise<ZoneRate[] | ErrorResponse> {
  try {
    console.log(`获取区域价格，产品ID:`, productId);
    // 使用 BaseFee 替代 ZoneRate，通过获取 BaseFee 中的区域价格
    const response = await get('/api/v1/products/base-fees/', { params: { product_id: productId } });
    if (response?.data?.data && Array.isArray(response.data.data)) {
      // 从 BaseFee 中提取区域价格信息
      const zonePrices: ZoneRate[] = [];
      
      response.data.data.forEach((baseFee: any) => {
        // 检查 BaseFee 是否有区域价格
        if (baseFee.zone_prices) {
          // 遍历各个区域价格
          Object.keys(baseFee.zone_prices).forEach(zoneKey => {
            if (zoneKey.startsWith('zone')) {
              const zoneNum = zoneKey.replace('zone', '');
              const zone = `ZONE${zoneNum}`;
              const price = baseFee.zone_prices[zoneKey];
              
              // 兼容旧的 ZoneRate 接口格式
              zonePrices.push({
                id: `${baseFee.id}_${zone}`,
                product_id: baseFee.product_id,
                weight_band_id: baseFee.id,
                zone,
                base_rate: price,
                effective_date: baseFee.effective_date || new Date().toISOString().split('T')[0],
                expiration_date: baseFee.expiration_date || '2099-12-31',
                status: baseFee.status || true,
                created_at: baseFee.created_at || new Date().toISOString(),
                updated_at: baseFee.updated_at
              });
            }
          });
        }
      });
      
      return zonePrices;
    }
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取区域价格失败:', error);
    return []; // 错误时返回空数组
  }
}

// 获取附加费
export async function getSurcharges(productId: string): Promise<Surcharge[] | ErrorResponse> {
  try {
    console.log(`获取附加费，产品ID:`, productId);
    const response = await get('/api/v1/products/surcharges/by_product/', { params: { product_id: productId } });
    if (response?.data && Array.isArray(response.data)) {
      return response.data;
    }
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取附加费失败:', error);
    return []; // 错误时返回空数组
  }
}

// 获取旺季附加费
export async function getSeasonalFees(productId: string): Promise<PeakSeasonSurcharge[] | ErrorResponse> {
  try {
    console.log(`获取旺季附加费，产品ID:`, productId);
    const response = await get('/api/v1/products/peak-season-surcharges/by_product/', { params: { product_id: productId } });
    if (response?.data && Array.isArray(response.data)) {
      return response.data;
    }
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取旺季附加费失败:', error);
    return []; // 错误时返回空数组
  }
}

// 基础费率相关API
export async function createBaseFee(data: WeightBand): Promise<WeightBand | ErrorResponse> {
  return post('/api/v1/products/base-fees/', data);
}

export async function updateBaseFee(id: string | number, data: Partial<WeightBand>): Promise<WeightBand | ErrorResponse> {
  return put(`/api/v1/products/base-fees/${id}/`, data);
}

export async function deleteBaseFee(id: string | number): Promise<void> {
  await del(`/api/v1/products/base-fees/${id}/`);
}

// 附加费相关API
export async function createSurcharge(data: Surcharge): Promise<Surcharge | ErrorResponse> {
  return post('/api/v1/products/surcharges/', data);
}

export async function updateSurcharge(id: string | number, data: Partial<Surcharge>): Promise<Surcharge | ErrorResponse> {
  return put(`/api/v1/products/surcharges/${id}/`, data);
}

export async function deleteSurcharge(id: string | number): Promise<void> {
  await del(`/api/v1/products/surcharges/${id}/`);
}

// 旺季附加费相关API
export async function createSeasonalFee(data: Partial<PeakSeasonSurcharge>): Promise<PeakSeasonSurcharge | ErrorResponse> {
  return post('/api/v1/products/peak-season-surcharges/', data);
}

export async function updateSeasonalFee(id: string | number, data: Partial<PeakSeasonSurcharge>): Promise<PeakSeasonSurcharge | ErrorResponse> {
  return put(`/api/v1/products/peak-season-surcharges/${id}/`, data);
}

export async function deleteSeasonalFee(id: string | number): Promise<void> {
  await del(`/api/v1/products/peak-season-surcharges/${id}/`);
}

// 增值服务相关API
export async function createValueAddedService(data: SpecialRule): Promise<SpecialRule | ErrorResponse> {
  return post('/api/v1/products/value-added-services/', data);
}

export async function updateValueAddedService(id: string | number, data: Partial<SpecialRule>): Promise<SpecialRule | ErrorResponse> {
  return put(`/api/v1/products/value-added-services/${id}/`, data);
}

export async function deleteValueAddedService(id: string | number): Promise<void> {
  await del(`/api/v1/products/value-added-services/${id}/`);
}

// 创建重量范围
export const createWeightRange = (data: Partial<WeightRange>) => {
  return post('/api/v1/products/weight-ranges/', data);
};

// 更新重量范围
export const updateWeightRange = (id: string | number, data: Partial<WeightRange>) => {
  return put(`/api/v1/products/weight-ranges/${id}/`, data);
};

// 删除重量范围
export const deleteWeightRange = async (id: string | number): Promise<void> => {
  await del(`/api/v1/products/weight-ranges/${id}/`);
};

// 获取特殊规则
export async function getSpecialRules(productId: string): Promise<any> {
  try {
    console.log(`获取特殊规则，产品ID:`, productId);
    const response = await get('/api/v1/products/special-rules/', { params: { product_id: productId } });
    if (response?.data?.data && Object.keys(response.data.data).length > 0) {
      return Object.values(response.data.data);
    }
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取特殊规则失败:', error);
    return []; // 错误时返回空数组
  }
}

// 获取增值服务
export async function getValueAddedServices(productId: string): Promise<any> {
  try {
    console.log(`获取增值服务，产品ID:`, productId);
    const response = await get('/api/v1/products/value-added-services/', { params: { product_id: productId } });
    if (response?.data?.data && Object.keys(response.data.data).length > 0) {
      return Object.values(response.data.data);
    }
    return []; // 返回空数组而不是undefined
  } catch (error) {
    console.error('获取增值服务失败:', error);
    return []; // 错误时返回空数组
  }
}

// 检查单个产品数据完整性
export async function checkProductIntegrity(data: {product_id: string | number; dry_run?: boolean}): Promise<any> {
  try {
    const { product_id, dry_run = true } = data;
    console.log(`检查产品数据完整性，产品ID: ${product_id}, 干运行: ${dry_run}`);
    const endpoint = `/api/v1/products/fix-product-integrity/${product_id}/`;
    const response = await post(endpoint, {}, { params: { dry_run } });
    return response.data;
  } catch (error) {
    console.error('检查产品数据完整性失败:', error);
    throw error;
  }
}

// 批量检查产品数据完整性
export async function batchCheckIntegrity(data: {product_ids: (string | number)[]; dry_run?: boolean}): Promise<any> {
  try {
    const { product_ids, dry_run = true } = data;
    console.log(`批量检查产品数据完整性，产品IDs: ${product_ids.join(', ')}, 干运行: ${dry_run}`);
    const endpoint = `/api/v1/products/fix-product-integrity/`;
    const response = await post(endpoint, { product_ids }, { params: { dry_run } });
    return response.data;
  } catch (error) {
    console.error('批量检查产品数据完整性失败:', error);
    throw error;
  }
}

// 上传产品Excel文件
export async function uploadProductExcel(file: File): Promise<any> {
  try {
    console.log('开始上传产品Excel文件');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await post('/api/v1/products/products/upload_product_excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('上传产品Excel文件失败:', error);
    throw error;
  }
}

// 下载产品模板
export async function downloadProductTemplate(): Promise<Blob> {
  try {
    console.log('开始下载产品Excel模板');
    const response = await get('/api/v1/products/download-product-template/', {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error('下载产品Excel模板失败:', error);
    throw error;
  }
}

export async function getPublicProducts(): Promise<ProductListResponse> {
  try {
    console.log('开始请求公开产品列表');
    
    // 添加当前时间戳防止缓存
    const timestamp = new Date().getTime();
    const params = { t: timestamp }; 
    
    const response = await get('/api/v1/public/products/', { params }) as any;
    
    console.log('API原始响应:', response);
    
    // 处理响应数据
    if (response && response.results) {
      return {
        items: response.results,
        total: response.count || 0,
        page: 1,
        page_size: response.results.length
      } as ProductListResponse;
    }
    
    // 无法解析时返回空结果
    console.warn('无法从响应中提取产品数据，返回空列表');
    return {
      items: [],
      total: 0,
      page: 1, 
      page_size: 10
    } as ProductListResponse;
  } catch (error) {
    console.error('获取公开产品列表出错:', error);
    return {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      error: String(error)
    } as unknown as ProductListResponse;
  }
}

// 获取产品基础费率
export async function getProductBaseFees(productId: string) {
  try {
    console.log('获取产品基础费率，ID:', productId);
    const response = await get('/api/v1/products/base-fees/by_product/', { params: { product_id: productId } });
    console.log('获取产品基础费率响应:', response);
    return response.data;
  } catch (error) {
    console.error('获取产品基础费率失败:', error);
    throw error;
  }
}

// 获取产品附加费
export async function getProductSurcharges(productId: string) {
  try {
    console.log('获取产品附加费，ID:', productId);
    const response = await get('/api/v1/products/surcharges/by_product/', { params: { product_id: productId } });
    console.log('获取产品附加费响应:', response);
    return response.data;
  } catch (error) {
    console.error('获取产品附加费失败:', error);
    throw error;
  }
}

// 获取产品旺季附加费
export async function getProductPeakSeasonSurcharges(productId: string) {
  try {
    console.log('获取产品旺季附加费，ID:', productId);
    const response = await get('/api/v1/products/peak-season-surcharges/by_product/', { params: { product_id: productId } });
    console.log('获取产品旺季附加费响应:', response);
    return response.data;
  } catch (error) {
    console.error('获取产品旺季附加费失败:', error);
    throw error;
  }
}

// 更新产品基础费率
export async function updateProductBaseFees(productId: string, baseFeesData: any[]) {
  try {
    console.log('更新产品基础费率，ID:', productId, '数据:', baseFeesData);
    const data = {
      product_id: productId,
      base_fees: baseFeesData
    };
    const response = await put('/api/v1/products/base-fees/by_product/', data);
    console.log('更新产品基础费率响应:', response);
    return response.data;
  } catch (error) {
    console.error('更新产品基础费率失败:', error);
    throw error;
  }
}

// 更新产品附加费
export async function updateProductSurcharges(productId: string, surchargesData: any[]) {
  try {
    console.log('更新产品附加费，ID:', productId, '数据:', surchargesData);
    const data = {
      product_id: productId,
      surcharges: surchargesData
    };
    const response = await post('/api/v1/products/surcharges/by_product/', data);
    console.log('更新产品附加费响应:', response);
    return response.data;
  } catch (error) {
    console.error('更新产品附加费失败:', error);
    throw error;
  }
}

// 更新产品旺季附加费
export async function updateProductPeakSeasonSurcharges(productId: string, peakSeasonData: any[]) {
  try {
    console.log('更新产品旺季附加费，ID:', productId, '数据:', peakSeasonData);
    const data = {
      product_id: productId,
      peak_season_surcharges: peakSeasonData
    };
    const response = await post('/api/v1/products/peak-season-surcharges/by_product/', data);
    console.log('更新产品旺季附加费响应:', response);
    return response.data;
  } catch (error) {
    console.error('更新产品旺季附加费失败:', error);
    throw error;
  }
}

/**
 * 处理API响应数据，确保返回数组
 * @param response API响应数据
 * @returns 处理后的数组数据
 */
export function ensureArray(response: any): any[] {
  if (!response) {
    return [];
  }
  
  if (Array.isArray(response)) {
    return response;
  }
  
  // 如果response是对象，尝试从常见属性中提取数组
  if (typeof response === 'object') {
    // 尝试从常见属性中提取数组
    if (response.data && Array.isArray(response.data)) {
      return response.data;
    }
    
    if (response.items && Array.isArray(response.items)) {
      return response.items;
    }
    
    if (response.results && Array.isArray(response.results)) {
      return response.results;
    }
    
    if (response.list && Array.isArray(response.list)) {
      return response.list;
    }
    
    // 尝试查找surcharges相关的属性
    if (response.surcharges && Array.isArray(response.surcharges)) {
      return response.surcharges;
    }
    
    if (response.peak_season_surcharges && Array.isArray(response.peak_season_surcharges)) {
      return response.peak_season_surcharges;
    }
    
    if (response.base_fees && Array.isArray(response.base_fees)) {
      return response.base_fees;
    }
  }
  
  // 如果无法提取数组，返回空数组
  console.warn('无法从API响应中提取数组数据:', response);
  return [];
}
