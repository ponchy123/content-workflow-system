/**
 * 转换后端日期格式为前端显示格式
 * @param dateString 后端日期字符串（ISO格式）
 * @param format 目标格式（默认：YYYY-MM-DD）
 */
export function formatDate(dateString: string | null | undefined, format = 'YYYY-MM-DD'): string {
  if (!dateString) return '';

  try {
    const date = new Date(dateString);

    // 简单的格式化实现
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    // 根据请求的格式返回
    switch (format) {
      case 'YYYY-MM-DD':
        return `${year}-${month}-${day}`;
      case 'YYYY-MM-DD HH:mm':
        return `${year}-${month}-${day} ${hours}:${minutes}`;
      case 'YYYY-MM-DD HH:mm:ss':
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      case 'MM/DD/YYYY':
        return `${month}/${day}/${year}`;
      default:
        return `${year}-${month}-${day}`;
    }
  } catch (error) {
    console.error('Date formatting error:', error);
    return dateString as string;
  }
}

/**
 * 将枚举值从后端格式转换为前端显示格式
 * @param value 枚举值
 * @param enumMap 枚举映射表
 * @param defaultValue 默认值
 */
export function mapEnumValue<T extends string | number>(
  value: T | null | undefined,
  enumMap: Record<string, string>,
  defaultValue = '未知',
): string {
  if (value === null || value === undefined) return defaultValue;
  return enumMap[value.toString()] || defaultValue;
}

/**
 * 将后端数据转换为前端显示格式
 * @param data 后端数据
 * @param transformers 字段转换器
 */
export function transformResponseData<T extends Record<string, any>>(
  data: T,
  transformers: Record<keyof T, (value: any) => any>,
): T {
  if (!data || typeof data !== 'object') return data;

  const result = { ...data } as T;

  // 应用转换器
  Object.keys(transformers).forEach(key => {
    const field = key as keyof T;
    if (field in data && typeof transformers[field] === 'function') {
      result[field] = transformers[field](data[field]);
    }
  });

  return result;
}

/**
 * 将前端表单数据转换为后端请求格式
 * @param formData 表单数据
 * @param transformers 字段转换器
 */
export function transformRequestData<T extends Record<string, any>>(
  formData: T,
  transformers: Record<keyof T, (value: any) => any>,
): T {
  if (!formData || typeof formData !== 'object') return formData;

  const result = { ...formData } as T;

  // 应用转换器
  Object.keys(transformers).forEach(key => {
    const field = key as keyof T;
    if (field in formData && typeof transformers[field] === 'function') {
      result[field] = transformers[field](formData[field]);
    }
  });

  return result;
}

/**
 * 处理嵌套对象或数组
 * @param data 源数据
 * @param path 属性路径（如 'user.address.city' 或 'items[0].name'）
 * @param defaultValue 默认值
 */
export function getNestedValue<T>(data: Record<string, any>, path: string, defaultValue: T): T {
  if (!data || typeof data !== 'object') return defaultValue;
  if (!path) return data as unknown as T;

  try {
    // 处理数组索引和嵌套属性
    const parts = path.replace(/\[([^\]]*)\]/g, '.$1').split('.');
    let result: any = data;

    for (const part of parts) {
      if (part in result) {
        result = result[part];
      } else {
        return defaultValue;
      }
    }

    return result === undefined ? defaultValue : result;
  } catch (error) {
    console.error('Error getting nested value:', error);
    return defaultValue;
  }
}

/**
 * 创建常用的状态枚举映射
 * @param customMapping 自定义映射
 */
export function createStatusMapping(
  customMapping: Record<string, string> = {},
): Record<string, string> {
  const defaultMapping: Record<string, string> = {
    active: '激活',
    inactive: '禁用',
    pending: '待处理',
    approved: '已批准',
    rejected: '已拒绝',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消',
    error: '错误',
  };

  return { ...defaultMapping, ...customMapping };
}
