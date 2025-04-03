import type { BatchCalculationItem, ValidationResult } from '@/types/calculator';
import type { 
  Product, 
  ProductRule,
  WeightBand,
  ZoneRate,
  Surcharge,
  PeakSeasonSurcharge,
  WeightUnit,
  DimUnit,
  PricingType,
  ChargeType
} from '@/types/product';
import { WEIGHT_UNITS, DIM_UNITS, PRICING_TYPES, CHARGE_TYPES } from '@/types/product';

export interface TemplateField {
  key: string;
  name: string;
  example: string | number;
  required: boolean;
  type: 'string' | 'number';
  min?: number;
  integer?: boolean;
}

export const batchCalculationTemplate: TemplateField[] = [
  {
    key: 'fromAddress',
    name: '发货地',
    example: '广州市天河区',
    required: true,
    type: 'string',
  },
  {
    key: 'toAddress',
    name: '收货地',
    example: '北京市朝阳区',
    required: true,
    type: 'string',
  },
  {
    key: 'weight',
    name: '重量(kg)',
    example: '1.5',
    required: true,
    type: 'number',
    min: 0.01,
  },
  {
    key: 'volume',
    name: '体积(m³)',
    example: '0.008',
    required: false,
    type: 'number',
    min: 0,
  },
  {
    key: 'quantity',
    name: '数量',
    example: '1',
    required: true,
    type: 'number',
    min: 1,
    integer: true,
  },
  {
    key: 'ruleId',
    name: '产品规则',
    example: 'RULE001',
    required: true,
    type: 'string',
  },
  {
    key: 'note',
    name: '备注',
    example: '易碎品',
    required: false,
    type: 'string',
  },
];

export function validateBatchData(
  data: Record<string, any>[],
  productRules: ProductRule[],
): ValidationResult {
  const errors: Array<{ row: number; field: string; message: string }> = [];
  const warnings: Array<{ row: number; field: string; message: string }> = [];
  const validData: BatchCalculationItem[] = [];

  // 验证数据不能为空
  if (!data || data.length === 0) {
    errors.push({
      row: 0,
      field: 'file',
      message: '文件内容为空',
    });
    return {
      isValid: false,
      data: [],
      errors,
      warnings,
    };
  }

  // 验证每一行数据
  data.forEach((row, index) => {
    const rowNumber = index + 1;
    const item: Record<string, any> = {};
    let hasError = false;

    // 验证每个字段
    batchCalculationTemplate.forEach(field => {
      const value = row[field.key];

      // 验证必填字段
      if (field.required && (value === undefined || value === null || value === '')) {
        errors.push({
          row: rowNumber,
          field: field.key,
          message: `${field.name}不能为空`,
        });
        hasError = true;
        return;
      }

      // 验证数字类型
      if (field.type === 'number' && value !== undefined && value !== '') {
        const numValue = Number(value);
        if (isNaN(numValue)) {
          errors.push({
            row: rowNumber,
            field: field.key,
            message: `${field.name}必须是数字`,
          });
          hasError = true;
          return;
        }

        if (field.min !== undefined && numValue < field.min) {
          errors.push({
            row: rowNumber,
            field: field.key,
            message: `${field.name}不能小于${field.min}`,
          });
          hasError = true;
          return;
        }

        if (field.integer && !Number.isInteger(numValue)) {
          errors.push({
            row: rowNumber,
            field: field.key,
            message: `${field.name}必须是整数`,
          });
          hasError = true;
          return;
        }

        item[field.key] = numValue;
      } else {
        item[field.key] = value;
      }
    });

    // 验证产品规则是否存在
    if (item.ruleId && !productRules.some(rule => rule.id === item.ruleId)) {
      errors.push({
        row: rowNumber,
        field: 'ruleId',
        message: '产品规则不存在',
      });
      hasError = true;
    }

    // 添加警告
    if (item.weight && item.weight > 100) {
      warnings.push({
        row: rowNumber,
        field: 'weight',
        message: '重量超过100kg，请确认是否正确',
      });
    }

    if (!hasError) {
      validData.push(item as unknown as BatchCalculationItem);
    }
  });

  return {
    isValid: errors.length === 0,
    data: validData,
    errors,
    warnings,
  };
}

// 邮政编码验证
export const validatePostalCode = (
  postalCode: string,
  format: 'auto' | 'us' | 'cn' = 'auto'
): { valid: boolean; message?: string } => {
  if (!postalCode.trim()) {
    return { valid: false, message: '邮政编码不能为空' };
  }

  // 移除位数限制，接受任何非空邮编
  return { valid: true };
};

/**
 * 验证日期字符串格式是否正确
 * @param date 日期字符串
 * @returns boolean
 */
export function isValidDate(date: string): boolean {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(date)) return false;
  
  const d = new Date(date);
  return d instanceof Date && !isNaN(d.getTime());
}

/**
 * 验证数值范围
 * @param value 数值
 * @param min 最小值
 * @param max 最大值
 * @returns boolean
 */
export function isValidNumber(value: number, min?: number, max?: number): boolean {
  if (typeof value !== 'number' || isNaN(value)) return false;
  if (min !== undefined && value < min) return false;
  if (max !== undefined && value > max) return false;
  return true;
}

/**
 * 验证产品基础数据
 * @param data 产品数据
 * @returns { valid: boolean, errors: string[] }
 */
export function validateProduct(data: Partial<Product>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 验证必填字段
  if (!data.code) errors.push('产品代码不能为空');
  if (!data.name) errors.push('产品名称不能为空');
  if (!data.provider) errors.push('服务商不能为空');
  if (!data.dim_factor) errors.push('体积重系数不能为空');
  if (!data.effective_date) errors.push('生效日期不能为空');
  if (!data.expiration_date) errors.push('失效日期不能为空');

  // 验证日期格式
  if (data.effective_date && !isValidDate(data.effective_date)) {
    errors.push('生效日期格式不正确，应为YYYY-MM-DD');
  }
  if (data.expiration_date && !isValidDate(data.expiration_date)) {
    errors.push('失效日期格式不正确，应为YYYY-MM-DD');
  }

  // 验证日期逻辑
  if (data.effective_date && data.expiration_date) {
    if (new Date(data.effective_date) > new Date(data.expiration_date)) {
      errors.push('生效日期不能晚于失效日期');
    }
  }

  // 验证体积重系数
  if (data.dim_factor && !isValidNumber(data.dim_factor, 0)) {
    errors.push('体积重系数必须大于0');
  }

  // 验证单位
  if (data.weight_unit && !WEIGHT_UNITS.includes(data.weight_unit as WeightUnit)) {
    errors.push('重量单位不正确，应为KG或LB');
  }
  if (data.dim_unit && !DIM_UNITS.includes(data.dim_unit as DimUnit)) {
    errors.push('尺寸单位不正确，应为CM或IN');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 验证重量段数据
 * @param data 重量段数据
 * @returns { valid: boolean, errors: string[] }
 */
export function validateWeightBand(data: Partial<WeightBand>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 验证必填字段
  if (!data.product_id) errors.push('产品ID不能为空');
  if (data.min_weight === undefined) errors.push('最小重量不能为空');
  if (!data.pricing_type) errors.push('计价类型不能为空');

  // 验证重量范围
  if (data.min_weight !== undefined && !isValidNumber(data.min_weight, 0)) {
    errors.push('最小重量必须大于0');
  }
  if (data.max_weight !== undefined && data.max_weight !== null && !isValidNumber(data.max_weight, data.min_weight)) {
    errors.push('最大重量必须大于最小重量');
  }

  // 验证计价类型
  if (data.pricing_type && !PRICING_TYPES.includes(data.pricing_type)) {
    errors.push('计价类型不正确，应为STEP或LINEAR');
  }

  // 验证日期
  if (data.effective_date && !isValidDate(data.effective_date)) {
    errors.push('生效日期格式不正确');
  }
  if (data.expiration_date && !isValidDate(data.expiration_date)) {
    errors.push('失效日期格式不正确');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 验证区域费率数据
 * @deprecated 请直接使用 BaseFee 的区域价格，此函数仅为兼容旧代码保留
 * @param data 区域费率数据
 * @returns { valid: boolean, errors: string[] }
 */
export function validateZoneRate(data: Partial<ZoneRate>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 验证必填字段
  if (!data.product_id) errors.push('产品ID不能为空');
  if (!data.weight_band_id) errors.push('重量段ID不能为空');
  if (!data.zone) errors.push('区域不能为空');
  if (data.base_rate === undefined) errors.push('基础费率不能为空');

  // 验证费率
  if (data.base_rate !== undefined && !isValidNumber(data.base_rate, 0)) {
    errors.push('基础费率必须大于0');
  }

  // 验证日期
  if (data.effective_date && !isValidDate(data.effective_date)) {
    errors.push('生效日期格式不正确');
  }
  if (data.expiration_date && !isValidDate(data.expiration_date)) {
    errors.push('失效日期格式不正确');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 验证附加费数据
 * @param data 附加费数据
 * @returns { valid: boolean, errors: string[] }
 */
export function validateSurcharge(data: Partial<Surcharge>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 验证必填字段
  if (!data.product_id) errors.push('产品ID不能为空');
  if (!data.name) errors.push('附加费名称不能为空');
  if (!data.surcharge_type) errors.push('附加费类型不能为空');
  if (data.amount === undefined) errors.push('金额不能为空');

  // 验证金额范围
  if (data.amount !== undefined) {
    if (data.surcharge_type === 'percentage' && !isValidNumber(data.amount, 0, 100)) {
      errors.push('百分比必须在0-100之间');
    } else if (data.surcharge_type === 'fixed' && !isValidNumber(data.amount, 0)) {
      errors.push('固定金额必须大于0');
    }
  }

  // 验证日期
  if (data.effective_date && !isValidDate(data.effective_date)) {
    errors.push('生效日期格式不正确');
  }
  if (data.expiration_date && !isValidDate(data.expiration_date)) {
    errors.push('失效日期格式不正确');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 验证旺季附加费数据
 * @param data 旺季附加费数据
 * @returns { valid: boolean, errors: string[] }
 */
export function validatePeakSeasonSurcharge(data: Partial<PeakSeasonSurcharge>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 验证必填字段
  if (!data.product_id) errors.push('产品ID不能为空');
  if (!data.surcharge_type) errors.push('附加费类型不能为空');
  if (!data.start_date) errors.push('开始日期不能为空');
  if (!data.end_date) errors.push('结束日期不能为空');
  if (data.fee_amount === undefined) errors.push('费用金额不能为空');

  // 验证金额
  if (data.fee_amount !== undefined && !isValidNumber(data.fee_amount, 0)) {
    errors.push('费用金额必须大于0');
  }

  // 验证日期
  if (data.start_date && !isValidDate(data.start_date)) {
    errors.push('开始日期格式不正确');
  }
  if (data.end_date && !isValidDate(data.end_date)) {
    errors.push('结束日期格式不正确');
  }
  if (data.start_date && data.end_date) {
    if (new Date(data.start_date) > new Date(data.end_date)) {
      errors.push('开始日期不能晚于结束日期');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
