/**
 * 数据验证工具
 */

export interface ValidationRule {
  required?: boolean;
  min?: number;
  max?: number;
  pattern?: RegExp;
  message?: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface ValidationError {
  field: string;
  message: string;
}

export class Validator {
  private rules: Record<string, ValidationRule[]>;

  constructor(rules: Record<string, ValidationRule[]>) {
    this.rules = rules;
  }

  /**
   * 验证单个字段
   */
  async validateField(field: string, value: any): Promise<ValidationError[]> {
    const rules = this.rules[field];
    if (!rules) return [];

    const errors: ValidationError[] = [];

    for (const rule of rules) {
      // 必填验证
      if (rule.required && (value === undefined || value === null || value === '')) {
        errors.push({
          field,
          message: rule.message || `${field} 是必填项`,
        });
        continue;
      }

      // 最小值验证
      if (rule.min !== undefined && typeof value === 'number' && value < rule.min) {
        errors.push({
          field,
          message: rule.message || `${field} 不能小于 ${rule.min}`,
        });
      }

      // 最大值验证
      if (rule.max !== undefined && typeof value === 'number' && value > rule.max) {
        errors.push({
          field,
          message: rule.message || `${field} 不能大于 ${rule.max}`,
        });
      }

      // 正则验证
      if (rule.pattern && !rule.pattern.test(String(value))) {
        errors.push({
          field,
          message: rule.message || `${field} 格式不正确`,
        });
      }

      // 自定义验证
      if (rule.validator) {
        try {
          const result = await Promise.resolve(rule.validator(value));
          if (!result) {
            errors.push({
              field,
              message: rule.message || `${field} 验证失败`,
            });
          }
        } catch (error) {
          errors.push({
            field,
            message: error instanceof Error ? error.message : `${field} 验证出错`,
          });
        }
      }
    }

    return errors;
  }

  /**
   * 验证所有字段
   */
  async validate(data: Record<string, any>): Promise<ValidationError[]> {
    const errors: ValidationError[] = [];

    for (const field in this.rules) {
      const fieldErrors = await this.validateField(field, data[field]);
      errors.push(...fieldErrors);
    }

    return errors;
  }
}

/**
 * 常用验证规则
 */
export const commonRules = {
  required: {
    required: true,
    message: '此项是必填项',
  },
  email: {
    pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    message: '请输入有效的邮箱地址',
  },
  phone: {
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入有效的手机号码',
  },
  url: {
    pattern: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/,
    message: '请输入有效的URL地址',
  },
};
