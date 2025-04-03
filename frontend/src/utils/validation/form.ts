import { reactive, ref } from 'vue';
import type { FormInstance } from 'element-plus';
import type { Ref } from 'vue';
import { formRules } from '@/types/forms';

/**
 * 创建表单验证工具
 * @param formData 表单数据引用
 * @param rules 验证规则对象
 * @returns 表单验证相关的方法和对象
 */
export function useFormValidation<T extends Object>(formData: Ref<T>, rules?: Record<string, any>) {
  const formRef = ref<FormInstance>();
  const validating = ref(false);
  const errors = ref<Record<string, string>>({});

  // 默认使用 formRules 中的规则
  const defaultRules = {} as Record<string, any>;

  // 验证表单
  const validate = async (): Promise<boolean> => {
    if (!formRef.value) return false;

    validating.value = true;
    errors.value = {};

    try {
      await formRef.value.validate();
      return true;
    } catch (validationErrors: any) {
      if (validationErrors && typeof validationErrors === 'object') {
        const errs = {} as Record<string, string>;

        // 处理Element Plus的验证错误
        Object.entries(validationErrors).forEach(([field, fieldErrors]) => {
          if (Array.isArray(fieldErrors) && fieldErrors.length > 0) {
            const firstError = fieldErrors[0];
            if (typeof firstError === 'object' && 'message' in firstError) {
              errs[field] = firstError.message as string;
            }
          }
        });

        errors.value = errs;
      }
      return false;
    } finally {
      validating.value = false;
    }
  };

  // 重置表单
  const resetForm = () => {
    if (formRef.value) {
      formRef.value.resetFields();
    }
  };

  // 验证特定字段
  const validateField = async (field: string): Promise<boolean> => {
    if (!formRef.value) return false;

    try {
      await formRef.value.validateField(field);
      return true;
    } catch (error) {
      return false;
    }
  };

  return {
    formRef,
    validating,
    errors,
    validate,
    resetForm,
    validateField,
    rules: rules || defaultRules,
  };
}

/**
 * 创建表单处理逻辑
 * @param options 表单配置选项
 * @returns 表单相关的方法和属性
 */
export function useForm<T extends Object>({
  initialData,
  rules,
  onSubmit,
  onCancel,
}: {
  initialData?: Partial<T>;
  rules?: Record<string, any>;
  onSubmit?: (data: T) => void | Promise<void>;
  onCancel?: () => void;
}) {
  const formData = ref(initialData || {}) as Ref<T>;
  const loading = ref(false);

  const { formRef, validate, resetForm, errors } = useFormValidation(formData, rules);

  // 提交表单
  const handleSubmit = async () => {
    if (loading.value) return;

    const isValid = await validate();
    if (!isValid) return;

    loading.value = true;

    try {
      if (onSubmit) {
        await onSubmit(formData.value);
      }
    } finally {
      loading.value = false;
    }
  };

  // 取消
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  return {
    formRef,
    formData,
    loading,
    errors,
    handleSubmit,
    handleCancel,
    resetForm,
  };
}

/**
 * 创建动态表单项处理
 * @returns 动态表单项处理方法
 */
export function useDynamicFormItems<T>() {
  const addItem = (list: T[], item: T) => {
    list.push(item);
  };

  const removeItem = (list: T[], index: number) => {
    list.splice(index, 1);
  };

  const moveItem = (list: T[], fromIndex: number, toIndex: number) => {
    if (
      fromIndex < 0 ||
      fromIndex >= list.length ||
      toIndex < 0 ||
      toIndex >= list.length ||
      fromIndex === toIndex
    ) {
      return;
    }

    const item = list[fromIndex];
    list.splice(fromIndex, 1);
    list.splice(toIndex, 0, item);
  };

  return {
    addItem,
    removeItem,
    moveItem,
  };
}
