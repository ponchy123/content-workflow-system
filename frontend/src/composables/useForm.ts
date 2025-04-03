import { ref, reactive, computed, toRaw } from 'vue';
import type { Ref, UnwrapRef } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

export interface FormOptions<T> {
  initialValues?: Partial<T>;
  rules?: FormRules;
  validateOnChange?: boolean;
  transformSubmit?: (values: T) => any;
  onSubmitSuccess?: (data: any) => void;
  onSubmitError?: (error: any) => void;
  resetAfterSubmit?: boolean;
}

export function useForm<T extends Record<string, any>>(
  submitFn: (values: any) => Promise<any>,
  options: FormOptions<T> = {}
) {
  // 默认选项
  const defaultOptions: FormOptions<T> = {
    initialValues: {} as Partial<T>,
    rules: {},
    validateOnChange: false,
    transformSubmit: (values) => values,
    onSubmitSuccess: () => {},
    onSubmitError: (error) => {
      ElMessage.error(`提交失败: ${error.message || '未知错误'}`);
    },
    resetAfterSubmit: false,
  };

  // 合并选项
  const mergedOptions = { ...defaultOptions, ...options };

  // 表单状态
  const formRef = ref<FormInstance>();
  const formData = reactive({ ...mergedOptions.initialValues } as T);
  const formRules = reactive(mergedOptions.rules || {});
  const submitting = ref(false);
  const submitSuccess = ref(false);
  const submitError = ref<Error | null>(null);

  // 计算表单是否修改过
  const isFormDirty = ref(false);

  // 处理表单值变化
  const handleValueChange = () => {
    isFormDirty.value = true;
    if (mergedOptions.validateOnChange && formRef.value) {
      formRef.value.validate().catch(() => {});
    }
  };

  // 重置表单
  const resetForm = () => {
    if (formRef.value) {
      formRef.value.resetFields();
      Object.assign(formData, mergedOptions.initialValues);
      isFormDirty.value = false;
      submitSuccess.value = false;
      submitError.value = null;
    }
  };

  // 设置表单值
  const setFormValues = (values: Partial<T>) => {
    Object.assign(formData, values);
  };

  // 获取表单值副本（修复类型问题）
  const getFormValues = (): T => {
    return toRaw(formData) as unknown as T;
  };

  // 校验表单
  const validateForm = async (): Promise<boolean> => {
    if (!formRef.value) return false;
    
    try {
      await formRef.value.validate();
      return true;
    } catch (error) {
      return false;
    }
  };

  // 提交表单
  const submitForm = async () => {
    if (submitting.value) return;
    
    submitting.value = true;
    submitSuccess.value = false;
    submitError.value = null;
    
    try {
      // 校验表单
      const valid = await validateForm();
      if (!valid) {
        throw new Error('表单校验失败');
      }
      
      // 转换提交数据
      const rawData = toRaw(formData);
      const submitData = mergedOptions.transformSubmit
        ? mergedOptions.transformSubmit(rawData as unknown as T)
        : rawData;
      
      // 提交数据
      const result = await submitFn(submitData);
      
      submitSuccess.value = true;
      
      // 提交成功回调
      if (mergedOptions.onSubmitSuccess) {
        mergedOptions.onSubmitSuccess(result);
      }
      
      // 是否重置表单
      if (mergedOptions.resetAfterSubmit) {
        resetForm();
      } else {
        isFormDirty.value = false;
      }
      
      return result;
    } catch (error) {
      submitError.value = error as Error;
      
      // 提交失败回调
      if (mergedOptions.onSubmitError) {
        mergedOptions.onSubmitError(error);
      }
      
      throw error;
    } finally {
      submitting.value = false;
    }
  };

  return {
    // 状态和引用
    formRef,
    formData,
    formRules,
    submitting,
    submitSuccess,
    submitError,
    isFormDirty,
    
    // 方法
    handleValueChange,
    resetForm,
    setFormValues,
    getFormValues,
    validateForm,
    submitForm,
  };
}
