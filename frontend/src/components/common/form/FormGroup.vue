<template>
  <div class="form-group" :class="{ 'is-vertical': vertical }">
    <!-- 表单标题 -->
    <div v-if="title || $slots.title" class="form-group__title">
      <slot name="title">{{ title }}</slot>
    </div>

    <!-- 表单内容 -->
    <div class="form-group__content">
      <el-form
        ref="formRef"
        v-bind="formProps"
        :model="model"
        :rules="rules"
        :label-position="labelPosition"
        :label-width="labelWidth"
        :label-suffix="labelSuffix"
        :hide-required-asterisk="hideRequiredAsterisk"
        :show-message="showMessage"
        :inline-message="inlineMessage"
        :status-icon="statusIcon"
        :validate-on-rule-change="validateOnRuleChange"
        :size="size"
        :disabled="disabled"
        :scroll-to-error="scrollToError"
      >
        <slot />
      </el-form>
    </div>

    <!-- 表单操作 -->
    <div v-if="$slots.actions" class="form-group__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import type { FormInstance } from 'element-plus';

  interface Props {
    model: Record<string, any>;
    rules?: Record<string, any>;
    title?: string;
    vertical?: boolean;
    labelPosition?: 'right' | 'left' | 'top';
    labelWidth?: string | number;
    labelSuffix?: string;
    hideRequiredAsterisk?: boolean;
    showMessage?: boolean;
    inlineMessage?: boolean;
    statusIcon?: boolean;
    validateOnRuleChange?: boolean;
    size?: 'large' | 'default' | 'small';
    disabled?: boolean;
    scrollToError?: boolean;
    formProps?: Record<string, any>;
  }

  const props = withDefaults(defineProps<Props>(), {
    rules: () => ({}),
    vertical: false,
    labelPosition: 'right',
    labelWidth: 'auto',
    labelSuffix: '',
    hideRequiredAsterisk: false,
    showMessage: true,
    inlineMessage: false,
    statusIcon: false,
    validateOnRuleChange: true,
    size: 'default',
    disabled: false,
    scrollToError: false,
    formProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'validate', prop: string, isValid: boolean, message?: string): void;
  }>();

  const formRef = ref<FormInstance>();

  // 表单验证
  const validate = async (callback?: (isValid: boolean) => void) => {
    if (!formRef.value) return;
    try {
      const valid = await formRef.value.validate();
      callback?.(valid);
      return valid;
    } catch (error) {
      callback?.(false);
      return false;
    }
  };

  // 重置表单
  const resetFields = () => {
    formRef.value?.resetFields();
  };

  // 清除验证
  const clearValidate = (props?: string | string[]) => {
    formRef.value?.clearValidate(props);
  };

  // 验证字段
  const validateField = async (props: string | string[], callback?: (isValid: boolean) => void) => {
    if (!formRef.value) return;
    try {
      await formRef.value.validateField(props);
      callback?.(true);
      return true;
    } catch (error) {
      callback?.(false);
      return false;
    }
  };

  // 滚动到指定字段
  const scrollToField = (prop: string) => {
    formRef.value?.scrollToField(prop);
  };

  // 对外暴露方法
  defineExpose({
    validate,
    resetFields,
    clearValidate,
    validateField,
    scrollToField,
  });
</script>

<style>
  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background-color: var(--el-bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
  }

  .form-group__title {
    font-size: var(--font-size-large);
    font-weight: var(--font-weight-bold);
    color: var(--el-text-color-primary);
    line-height: 1.5;
  }

  .form-group__content {
    flex: 1;
  }

  .form-group__actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--el-border-color-lighter);
  }

  /* 垂直布局 */
  .form-group.is-vertical {
    .el-form {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .el-form-item {
      margin-bottom: 0;
    }
  }

  /* 暗色主题 */
  .dark .form-group {
    background-color: var(--el-bg-color-overlay);
    box-shadow: var(--box-shadow-dark);
  }
</style>
