import { get, post, put, del } from '@/api/core';
import type { PaginatedResponse } from '@/api/core/types';
import type {
  ZipZone,
  ZipZoneCreateRequest,
  ZipZoneUpdateRequest,
  ZipZoneListParams,
  RemoteArea,
  RemoteAreaCreateRequest,
  RemoteAreaUpdateRequest,
  RemoteAreaListParams,
  PostalCode,
  PostalSearchResult
} from '@/types/postal';
import type { ServiceProvider } from '@/types/core';
import type { ApiResponse } from '@/api/core';
import axios from 'axios';
import type { AxiosResponse } from 'axios';

export type {
  ZipZone,
  ZipZoneCreateRequest,
  ZipZoneUpdateRequest,
  ZipZoneListParams,
  RemoteArea,
  RemoteAreaCreateRequest,
  RemoteAreaUpdateRequest,
  RemoteAreaListParams,
  PostalCode,
  PostalSearchResult,
};

/**
 * 获取邮编分区列表
 * @param params - 查询参数
 * @returns 邮编分区列表及总数
 */
export const getZipZones = async (
  params: ZipZoneListParams,
): Promise<any> => {
  try {
    // 返回完整的API响应，不再进行解构
    const response = await get<any>('/api/v1/postcodes/zip-zones/', { params });
    console.log('API返回的原始邮编分区数据:', response);
    return response;
  } catch (error) {
    console.warn('Zip zones API not available, using mock data');
    // 返回模拟数据
    const defaultProvider: ServiceProvider = {
      id: 1,
      name: '默认服务商',
      code: 'DEFAULT',
      status: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    return {
      results: [
        {
          id: 1,
          provider_id: 1,
          provider: defaultProvider,
          origin_zip: '100000',
          dest_zip_start: '200000',
          dest_zip_end: '299999',
          zone_number: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: 'admin',
          updated_by: 'admin',
          is_deleted: false
        },
        {
          id: 2,
          provider_id: 1,
          provider: defaultProvider,
          origin_zip: '100000',
          dest_zip_start: '300000',
          dest_zip_end: '399999',
          zone_number: 3,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: 'admin',
          updated_by: 'admin',
          is_deleted: false
        }
      ],
      count: 2,
    };
  }
};

/**
 * 获取单个邮编分区详情
 * @param id - 邮编分区ID
 * @returns 邮编分区详情
 */
export const getZipZone = async (id: number): Promise<ZipZone> => {
  try {
    // 不再解构数据，直接返回完整响应
    const response = await get<ZipZone>(`/api/v1/postcodes/zip-zones/${id}/`);
    console.log('获取邮编分区详情响应:', response);
    
    // 检查响应格式，兼容不同的API响应结构
    if (response.data) {
      return response.data as ZipZone;
    } else {
      // 如果response本身就是ZipZone类型，直接返回
      return response as unknown as ZipZone;
    }
  } catch (error) {
    console.warn('Zip zone API not available, using mock data');
    const defaultProvider: ServiceProvider = {
      id: 1,
      name: '默认服务商',
      code: 'DEFAULT',
      status: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    return {
      id: id,
      provider_id: 1,
      provider: defaultProvider,
      origin_zip: '100000',
      dest_zip_start: '200000',
      dest_zip_end: '299999',
      zone_number: 2,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'admin',
      updated_by: 'admin',
      is_deleted: false
    };
  }
};

/**
 * 创建邮编分区
 * @param data - 创建数据
 * @returns 创建的邮编分区
 */
export const createZipZone = async (data: ZipZoneCreateRequest): Promise<ZipZone> => {
  const { data: response } = await post<ZipZone>('/api/v1/postcodes/zip-zones/', data);
  return response;
};

/**
 * 更新邮编分区
 * @param id - 邮编分区ID
 * @param data - 更新数据
 * @returns 更新后的邮编分区
 */
export const updateZipZone = async (
  id: number,
  data: ZipZoneUpdateRequest,
): Promise<ZipZone> => {
  const { data: response } = await put<ZipZone>(`/api/v1/postcodes/zip-zones/${id}/`, data);
  return response;
};

/**
 * 删除邮编分区
 * @param id - 邮编分区ID
 */
export const deleteZipZone = async (id: number): Promise<void> => {
  await del(`/api/v1/postcodes/zip-zones/${id}/`);
};

/**
 * 获取偏远地区列表
 * @param params - 查询参数
 * @returns 偏远地区列表及总数
 */
export const getRemoteAreas = async (
  params: RemoteAreaListParams,
): Promise<any> => {
  try {
    const response = await get<any>('/api/v1/postcodes/remote-areas/', { params });
    
    // 直接返回response.data，不再进行解构，保留完整的API响应格式
    return response;
  } catch (error) {
    console.warn('Remote areas API not available, using mock data');
    // 返回模拟数据
    const defaultProvider: ServiceProvider = {
      id: 1,
      name: '默认服务商',
      code: 'DEFAULT',
      status: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // 使用Django REST framework格式的模拟数据
    return {
      results: [
        {
          id: 1,
          provider_id: 1,
          provider: defaultProvider,
          origin_zip: '100000',
          zip_code: '650000',
          remote_level: '一级偏远',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: 'admin',
          updated_by: 'admin',
          is_deleted: false
        },
        {
          id: 2,
          provider_id: 1,
          provider: defaultProvider,
          origin_zip: '100000',
          zip_code: '850000',
          remote_level: '三级偏远',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: 'admin',
          updated_by: 'admin',
          is_deleted: false
        }
      ],
      count: 2
    };
  }
};

/**
 * 获取单个偏远地区详情
 * @param id - 偏远地区ID
 * @returns 偏远地区详情
 */
export const getRemoteArea = async (id: number): Promise<RemoteArea> => {
  try {
    console.log(`正在获取偏远地区详情，ID: ${id}`);
    const response = await get<RemoteArea>(`/api/v1/postcodes/remote-areas/${id}/`);
    console.log('API响应:', response);
    
    // 确保返回正确的数据结构
    const remoteAreaData = response.data || response;
    console.log('解析后的偏远地区数据:', remoteAreaData);
    
    return remoteAreaData;
  } catch (error) {
    console.error(`获取偏远地区详情失败，ID: ${id}`, error);
    console.warn('Remote area API not available, using mock data');
    
    const defaultProvider: ServiceProvider = {
      id: 1,
      name: '默认服务商',
      code: 'DEFAULT',
      status: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // 返回模拟数据
    return {
      id: id,
      provider_id: 1,
      provider: defaultProvider,
      origin_zip: '100000',
      zip_code: '650000',
      remote_level: '一级偏远',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'admin',
      updated_by: 'admin',
      is_deleted: false
    };
  }
};

/**
 * 创建偏远地区
 * @param data - 创建数据
 * @returns 创建的偏远地区
 */
export const createRemoteArea = async (data: RemoteAreaCreateRequest): Promise<RemoteArea> => {
  const { data: response } = await post<RemoteArea>('/api/v1/postcodes/remote-areas/', data);
  return response;
};

/**
 * 更新偏远地区
 * @param id - 偏远地区ID
 * @param data - 更新数据
 * @returns 更新后的偏远地区
 */
export const updateRemoteArea = async (
  id: number,
  data: RemoteAreaUpdateRequest,
): Promise<RemoteArea> => {
  const { data: response } = await put<RemoteArea>(`/api/v1/postcodes/remote-areas/${id}/`, data);
  return response;
};

/**
 * 删除偏远地区
 * @param id - 偏远地区ID
 */
export const deleteRemoteArea = async (id: number): Promise<any> => {
  try {
    console.log(`正在删除偏远地区，ID: ${id}`);
    const response = await del(`/api/v1/postcodes/remote-areas/${id}/`);
    console.log(`删除偏远地区成功，ID: ${id}，响应:`, response);
    return response;
  } catch (error) {
    console.error(`删除偏远地区失败，ID: ${id}`, error);
    // 将错误向上抛出，由调用者处理
    throw error;
  }
};

/**
 * 根据服务商、始发地邮编和目的地邮编查询分区号码
 * @param provider_id - 服务商ID
 * @param origin_zip - 始发地邮编
 * @param dest_zip - 目的地邮编
 * @returns 分区信息
 */
export const queryZoneByZip = async (
  provider_id: number,
  origin_zip: string,
  dest_zip: string
): Promise<ZipZone | null> => {
  try {
    console.log('查询邮编分区:', { provider_id, origin_zip, dest_zip });
    // 直接使用完整API路径，避免路由问题
    const response = await fetch(`/api/v1/postcodes/zip-zones/query/?provider_id=${provider_id}&origin_zip=${origin_zip}&dest_zip=${dest_zip}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      console.error('查询分区API错误:', response.status, response.statusText);
      return null;
    }
    
    const data = await response.json();
    console.log('查询分区返回数据:', data);
    return data;
  } catch (error) {
    console.error('查询分区信息失败:', error);
    return null;
  }
};

/**
 * 检查指定的服务商ID、始发地和目的地邮编组合是否已存在
 * @param provider_id 服务商ID
 * @param origin_zip 始发地邮编 
 * @param zip_code 偏远地区邮编
 * @param excludeId 排除的记录ID（编辑时排除自身）
 */
export async function checkRemoteAreaExists(
  provider_id: number,
  origin_zip: string,
  zip_code: string,
  excludeId?: number
): Promise<boolean> {
  try {
    // 使用特定条件查询已存在的记录
    const response = await getRemoteAreas({
      page: 1,
      page_size: 10,
      provider_id,
      origin_zip,
      zip_code
    });
    
    console.log('检查记录是否存在的API响应:', response);
    
    // 提取API响应数据
    const apiData = response.data || response;
    console.log('检查记录是否存在的处理数据:', apiData);
    
    // 查找结果数组
    let results: any[] = [];
    
    if (Array.isArray(apiData)) {
      results = apiData;
    } else if (apiData && typeof apiData === 'object') {
      if (apiData.results && Array.isArray(apiData.results)) {
        results = apiData.results;
      } else if (apiData.items && Array.isArray(apiData.items)) {
        results = apiData.items;
      } else if (apiData.data && Array.isArray(apiData.data)) {
        results = apiData.data;
      } else {
        // 查找可能的数组字段
        const arrayField = Object.entries(apiData).find(
          ([_, value]) => Array.isArray(value) && value.length > 0
        );
        if (arrayField) {
          results = arrayField[1] as any[];
        }
      }
    }
    
    // 如果有排除ID，过滤掉该记录
    if (excludeId && results.length > 0) {
      results = results.filter(item => item.id !== excludeId);
    }
    
    // 返回是否有匹配记录
    return results.length > 0;
  } catch (error) {
    console.error('检查偏远地区记录是否存在时出错:', error);
    // 如果查询出错，返回false以允许用户继续尝试
    return false;
  }
}

/**
 * 检查指定的邮编分区组合是否已存在
 * @param provider_id 服务商ID
 * @param origin_zip 始发地邮编
 * @param dest_zip_start 目的地邮编起始
 * @param dest_zip_end 目的地邮编终止
 * @param zone_number 分区号码
 * @param excludeId 排除的记录ID（编辑时排除自身）
 */
export async function checkZipZoneExists(
  provider_id: number,
  origin_zip: string,
  dest_zip_start: string,
  dest_zip_end: string,
  zone_number: number,
  excludeId?: number
): Promise<boolean> {
  try {
    console.log('检查邮编分区是否存在:', {
      provider_id,
      origin_zip,
      dest_zip_start,
      dest_zip_end,
      zone_number,
      excludeId
    });
    
    // 使用特定条件查询已存在的记录
    const response = await getZipZones({
      page: 1,
      page_size: 10,
      provider_id,
      origin_zip,
      zone_number
    });
    
    console.log('检查分区是否存在的API响应:', response);
    
    // 提取API响应数据
    let zipZones: ZipZone[] = [];
    
    // 使用PaginatedResponse的标准格式
    if (response.items && Array.isArray(response.items)) {
      zipZones = response.items;
    } 
    // 如果是其他格式的响应，做相应处理
    else if (response && typeof response === 'object' && 'results' in response && Array.isArray(response.results)) {
      zipZones = response.results as ZipZone[];
    } 
    // 处理直接返回数组的情况
    else if (Array.isArray(response)) {
      zipZones = response;
    }
    
    // 过滤符合条件的记录
    const filteredZones = zipZones.filter(zone => {
      // 排除当前编辑的记录
      if (excludeId && zone.id === excludeId) {
        return false;
      }
      
      // 精确匹配这些字段
      const matchProvider = zone.provider_id === provider_id;
      const matchOriginZip = zone.origin_zip === origin_zip;
      const matchDestZipStart = zone.dest_zip_start === dest_zip_start;
      const matchDestZipEnd = zone.dest_zip_end === dest_zip_end;
      const matchZoneNumber = zone.zone_number === zone_number;
      
      return matchProvider && matchOriginZip && matchDestZipStart && matchDestZipEnd && matchZoneNumber;
    });
    
    console.log('过滤后的结果:', filteredZones);
    
    // 返回是否有匹配记录
    return filteredZones.length > 0;
  } catch (error) {
    console.error('检查邮编分区记录是否存在时出错:', error);
    // 如果查询出错，返回false以允许用户继续尝试
    return false;
  }
}

/**
 * 导入邮编分区数据
 * @param file - 要上传的文件
 * @returns 导入结果
 */
export const importZipZones = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // 从localStorage获取token
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  
  if (!token) {
    throw new Error('请先登录后再进行导入操作');
  }
  
  console.log('开始导入文件，使用XMLHttpRequest');
  
  // 使用 XMLHttpRequest 代替 axios 进行文件上传
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    // 设置上传进度事件
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        console.log(`上传进度: ${percentComplete}%`);
      }
    };
    
    // 设置请求完成事件
    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        let response;
        try {
          response = JSON.parse(xhr.responseText);
        } catch (e) {
          response = {
            data: xhr.responseText,
            status: 'success'
          };
        }
        console.log('上传成功，响应:', response);
        resolve({ data: response });
      } else {
        console.error('上传失败，状态码:', xhr.status);
        let errorMessage = '上传失败';
        try {
          const errorResponse = JSON.parse(xhr.responseText);
          errorMessage = errorResponse.message || errorResponse.detail || '上传失败';
        } catch (e) {
          errorMessage = xhr.responseText || `上传失败，状态码：${xhr.status}`;
        }
        reject({
          response: {
            status: xhr.status,
            data: errorMessage
          },
          message: errorMessage
        });
      }
    };
    
    // 设置错误事件
    xhr.onerror = function() {
      console.error('请求错误');
      reject({
        message: '网络错误，请检查网络连接'
      });
    };
    
    // 打开请求
    xhr.open('POST', '/api/v1/postcodes/import-zip-zones/', true);
    
    // 添加请求头
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    // 不设置 Content-Type，让浏览器自动设置正确的 boundary
    
    // 发送请求
    xhr.send(formData);
  });
};

/**
 * 获取邮编列表
 * @param params
 * @returns
 */
export const getPostalCodes = async (params: any = {}) => {
  // 更正API路径
  try {
    const response = await get('/api/v1/postal/codes/', {
      params
    });
    
    // API正常返回数据
    return response;
  } catch (error) {
    console.error('获取邮编列表失败:', error);
    
    // 本地开发环境，使用模拟数据
    const isLocalhost = typeof window !== 'undefined' && window.location.hostname.includes('localhost');
    if (isLocalhost) {
      console.log('使用本地邮编模拟数据');
      return {
        results: [
          { postal_code: '100000' },
          { postal_code: '200000' },
          { postal_code: '300000' },
          { postal_code: '510000' },
          { postal_code: '610000' },
          { postal_code: '400000' }
        ],
        count: 6,
        page: 1,
        page_size: 10
      };
    }
    
    throw error;
  }
};

/**
 * 根据邮编获取地址
 * @param postalCode 
 * @returns 
 */
export const getAddressByPostalCode = async (postalCode: string) => {
  // 更正API路径
  try {
    const response = await get(`/api/v1/postal/address/${postalCode}/`);
    return response;
  } catch (error) {
    console.error('获取地址信息失败:', error);
    
    // 本地开发环境，使用模拟数据
    const isLocalhost = typeof window !== 'undefined' && window.location.hostname.includes('localhost');
    if (isLocalhost) {
      console.log('使用本地地址模拟数据');
      
      return {
        postal_code: postalCode
      };
    }
    
    throw error;
  }
};

/**
 * 搜索邮编
 * @param keyword 
 * @returns 
 */
export const searchPostalCode = async (keyword: string) => {
  // 更正API路径
  try {
    const response = await get(`/api/v1/postal/search/${keyword}/`);
    return response;
  } catch (error) {
    console.error('搜索邮编失败:', error);
    
    // 本地开发环境，使用模拟数据
    const isLocalhost = typeof window !== 'undefined' && window.location.hostname.includes('localhost');
    if (isLocalhost) {
      console.log('使用本地搜索模拟数据');
      return [
        { postal_code: '100000' },
        { postal_code: '200000' },
        { postal_code: '300000' },
        { postal_code: '510000' }
      ];
    }
    
    throw error;
  }
}; 