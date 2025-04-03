import type { BaseFee, WeightBand } from '@/types/product';

/**
 * 重量分组类型
 */
export interface WeightGroup {
  weight: number | string;
  unit: string;
  [key: string]: any; // 动态属性，用于存储各个分区的价格和ID
}

/**
 * 单元格表单数据类型
 */
export interface CellForm {
  weight: number | string;
  unit: string;
  zone: string;
  price: number;
  id?: string | number;
}

/**
 * 重量段表单数据类型
 */
export interface WeightForm {
  weight: number;
  unit: 'oz' | 'lb';
}

/**
 * 编辑重量段表单数据类型
 */
export interface EditWeightForm extends WeightForm {
  originalWeight: number;
  originalUnit: 'oz' | 'lb';
}

/**
 * 分区表单数据类型
 */
export interface ZoneForm {
  name: string;
  defaultPrice: number;
}

/**
 * 编辑分区表单数据类型
 */
export interface EditZoneForm {
  originalName: string;
  name: string;
}

/**
 * 基础费用表单组件属性类型
 */
export interface BaseFeeFormProps {
  productId: string;
  mode: 'add' | 'edit' | 'list';
  data: BaseFee | BaseFee[];
}

/**
 * 基础费用表单组件事件类型
 */
export interface BaseFeeFormEmits {
  (e: 'success'): void;
  (e: 'cancel'): void;
  (e: 'save'): void;
}