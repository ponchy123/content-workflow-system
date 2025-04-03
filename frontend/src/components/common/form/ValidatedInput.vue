<template>
  <el-form-item
    :prop="prop"
    :label="label"
    :rules="mergedRules"
    :required="required"
    :error="error"
    :show-message="showMessage"
    :inline-message="inlineMessage"
    :size="size"
  >
    <el-input
      ref="inputRef"
      v-model="inputValue"
      v-bind="inputProps"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :clearable="clearable"
      :show-password="showPassword"
      :maxlength="maxlength"
      :minlength="minlength"
      :show-word-limit="showWordLimit"
      :validate-event="validateEvent"
      @blur="handleBlur"
      @focus="handleFocus"
      @change="handleChange"
      @input="handleInput"
      @clear="handleClear"
    >
      <template v-if="$slots.prefix" #prefix>
        <slot name="prefix" />
      </template>
      <template v-if="$slots.suffix" #suffix>
        <slot name="suffix" />
      </template>
      <template v-if="$slots.prepend" #prepend>
        <slot name="prepend" />
      </template>
      <template v-if="$slots.append" #append>
        <slot name="append" />
      </template>
    </el-input>
  </el-form-item>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import type { FormItemRule } from 'element-plus';

  interface Props {
    modelValue?: string | number;
    prop?: string;
    label?: string;
    rules?: FormItemRule | FormItemRule[];
    required?: boolean;
    error?: string;
    showMessage?: boolean;
    inlineMessage?: boolean;
    size?: 'large' | 'default' | 'small';
    type?: string;
    placeholder?: string;
    disabled?: boolean;
    readonly?: boolean;
    clearable?: boolean;
    showPassword?: boolean;
    maxlength?: number;
    minlength?: number;
    showWordLimit?: boolean;
    validateEvent?: boolean;
    inputProps?: Record<string, any>;
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: '',
    type: 'text',
    showMessage: true,
    inlineMessage: false,
    size: 'default',
    clearable: false,
    showPassword: false,
    showWordLimit: false,
    validateEvent: true,
    inputProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string | number): void;
    (e: 'blur', event: Event): void;
    (e: 'focus', event: Event): void;
    (e: 'change', value: string | number): void;
    (e: 'input', value: string | number): void;
    (e: 'clear'): void;
  }>();

  const inputRef = ref();
  const inputValue = ref(props.modelValue);

  // 合并规则
  const mergedRules = computed(() => {
    if (!props.rules) return undefined;
    const rules = Array.isArray(props.rules) ? props.rules : [props.rules];
    if (props.required) {
      rules.unshift({ required: true, message: `请输入${props.label || ''}` });
    }
    return rules;
  });

  // 监听值变化
  watch(
    () => props.modelValue,
    val => {
      inputValue.value = val;
    },
  );

  watch(inputValue, val => {
    emit('update:modelValue', val);
  });

  // 事件处理
  const handleBlur = (event: Event) => {
    emit('blur', event);
  };

  const handleFocus = (event: Event) => {
    emit('focus', event);
  };

  const handleChange = (value: string | number) => {
    emit('change', value);
  };

  const handleInput = (value: string | number) => {
    emit('input', value);
  };

  const handleClear = () => {
    emit('clear');
  };

  // 对外暴露方法
  defineExpose({
    focus: () => inputRef.value?.focus(),
    blur: () => inputRef.value?.blur(),
    select: () => inputRef.value?.select(),
  });
</script>

<style>
  .el-form-item.is-error .el-input__wrapper {
    box-shadow: 0 0 0 1px var(--el-color-danger) inset;
  }

  .el-form-item.is-success .el-input__wrapper {
    box-shadow: 0 0 0 1px var(--el-color-success) inset;
  }

  /* 暗色主题 */
  .dark .el-form-item.is-error .el-input__wrapper {
    box-shadow: 0 0 0 1px var(--el-color-danger) inset;
  }

  .dark .el-form-item.is-success .el-input__wrapper {
    box-shadow: 0 0 0 1px var(--el-color-success) inset;
  }
</style>
