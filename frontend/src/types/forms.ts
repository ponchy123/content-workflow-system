import type { FormItemRule } from 'element-plus';

// 基础表单类型
export interface BaseForm {
  id?: string | number;
  createdAt?: string;
  updatedAt?: string;
}

// 基础表单属性
export interface BaseFormProps<T = any> {
  initialData?: Partial<T>;
  loading?: boolean;
  title?: string;
  hasSubmitButton?: boolean;
  hasCancelButton?: boolean;
  submitText?: string;
  cancelText?: string;
}

// 费率表单基础类型
export interface BaseRateForm extends BaseForm {
  effectiveDate: string;
  remark?: string;
}

// 燃油费率表单
export interface FuelRateForm extends BaseRateForm {
  rate: number;
}

// 邮编费率表单
export interface PostalRateForm extends BaseRateForm {
  zone: string;
  baseRate: number;
  remoteRateSurcharge: number;
}

// 区域表单
export interface RemoteAreaForm extends BaseRateForm {
  level: number;
  surchargeRate: number;
  zipCodes: ZipCode[];
}

// 分区表单
export interface ZoneForm extends BaseRateForm {
  zoneCode: string;
  zoneName: string;
  zoneType: string;
  zipRanges: ZipRange[];
  description: string;
  isEnabled: boolean;
}

// 邮编范围
export interface ZipRange {
  start: string;
  end: string;
}

// 邮编
export interface ZipCode {
  code: string;
  city: string;
}

// 表单验证规则
export const formRules = {
  // 必填规则
  required: (message = '此项为必填项'): FormItemRule => ({
    required: true,
    message,
    trigger: 'blur',
  }),

  // 数字规则
  number: (min = 0, message = `数值必须大于等于${min}`): FormItemRule => ({
    type: 'number' as const,
    min,
    message,
    trigger: 'blur',
  }),

  // 日期规则
  date: (message = '请选择日期'): FormItemRule => ({
    required: true,
    message,
    trigger: 'change',
  }),

  // 邮编规则
  zipCode: (message = '邮编格式不正确'): FormItemRule => ({
    pattern: /^\d{5,6}$/,
    message,
    trigger: 'blur',
  }),

  // 费率规则
  rate: [
    { required: true, message: '请输入费率', trigger: 'blur' },
    { type: 'number' as const, min: 0, message: '费率必须大于等于0', trigger: 'blur' },
  ],
};
