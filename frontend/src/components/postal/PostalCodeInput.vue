<template>
  <search-input
    v-model="inputValue"
    :name="name"
    :placeholder="placeholder"
    :label="label"
    :disabled="disabled"
    :required="required"
    :validator="validatePostalCode"
    :search-on-valid="true"
    :min-search-length="5"
    @update:modelValue="(val) => handleChange(val)"
    @search="(val) => handleSearch(val)"
    @valid="handleValid"
  />
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { SearchInput } from '@/components/common';
  import { validatePostalCode as validatePostalCodeUtil } from '@/utils/validation/validators';
  import type { PostalCode, PostalSearchResult } from '@/types/postal';

  interface Props {
    modelValue: string;
    name?: string;
    placeholder?: string;
    label?: string;
    disabled?: boolean;
    required?: boolean;
    format?: 'auto' | 'us' | 'cn';
  }

  const props = withDefaults(defineProps<Props>(), {
    name: 'postalCode',
    placeholder: '输入邮政编码',
    label: '',
    disabled: false,
    required: true,
    format: 'auto',
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void;
    (e: 'change', value: string): void;
    (e: 'search', value: string): void;
    (e: 'address-change', result: PostalSearchResult | null): void;
  }>();

  const inputValue = ref(props.modelValue);

  // 监听输入值变化
  watch(
    () => props.modelValue,
    newValue => {
      inputValue.value = newValue;
    },
  );

  // 验证函数
  const validatePostalCode = (value: string) => {
    return validatePostalCodeUtil(value, props.format);
  };

  // 处理值变化
  const handleChange = (value: string) => {
    emit('update:modelValue', value);
    emit('change', value);
  };

  // 处理验证结果
  const handleValid = (isValid: boolean) => {
    if (!isValid) {
      emit('address-change', null);
    }
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    emit('search', value);
    // 当值有效时，可能需要同时触发地址变更事件
    if (validatePostalCode(value).valid) {
      const addressInfo: PostalSearchResult = {
        postal_code: value,
        // 其他字段可能为空，等待搜索结果更新
      };
      emit('address-change', addressInfo);
    }
  };
</script>

<style scoped>
  .postal-code-input {
    margin-bottom: 1rem;
  }

  .is-invalid {
    border-color: var(--el-color-danger);
  }

  .error-message {
    color: var(--el-color-danger);
    font-size: 0.75rem;
    margin-top: 0.25rem;
  }
</style>
