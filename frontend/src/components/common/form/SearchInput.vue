<template>
  <div class="search-input" :class="{ 'is-focused': focused }">
    <el-input
      ref="inputRef"
      v-model="searchText"
      v-bind="inputProps"
      :placeholder="placeholder"
      :size="size"
      :disabled="disabled"
      :clearable="clearable"
      @focus="handleFocus"
      @blur="handleBlur"
      @clear="handleClear"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon class="search-input__icon">
          <search />
        </el-icon>
      </template>
      <template #suffix>
        <el-button
          v-if="showSearchButton"
          :size="size"
          type="primary"
          :disabled="disabled"
          @click="handleSearch"
        >
          {{ searchButtonText }}
        </el-button>
      </template>
    </el-input>

    <!-- 搜索建议 -->
    <div
      v-if="suggestions.length && focused"
      class="search-input__suggestions"
      :style="{ maxHeight: suggestionsMaxHeight }"
    >
      <ul class="search-input__suggestions-list">
        <li
          v-for="(item, index) in suggestions"
          :key="index"
          class="search-input__suggestion-item"
          :class="{ 'is-selected': index === selectedIndex }"
          @click="handleSelect(item)"
          @mouseenter="selectedIndex = index"
        >
          <slot name="suggestion" :item="item">
            {{ item }}
          </slot>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { Search } from '@element-plus/icons-vue';

  interface Props {
    modelValue?: string;
    placeholder?: string;
    size?: 'large' | 'default' | 'small';
    disabled?: boolean;
    clearable?: boolean;
    showSearchButton?: boolean;
    searchButtonText?: string;
    suggestions?: any[];
    suggestionsMaxHeight?: string;
    inputProps?: Record<string, any>;
    validator?: (value: string) => { valid: boolean; message?: string };
    searchOnValid?: boolean;
    minSearchLength?: number;
    name?: string;
    label?: string;
    required?: boolean;
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: '',
    placeholder: '请输入搜索内容',
    size: 'default',
    disabled: false,
    clearable: true,
    showSearchButton: false,
    searchButtonText: '搜索',
    suggestions: () => [],
    suggestionsMaxHeight: '300px',
    inputProps: () => ({}),
    validator: () => ({ valid: true }),
    searchOnValid: true,
    minSearchLength: 0,
    name: '',
    label: '',
    required: false,
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void;
    (e: 'search', value: string): void;
    (e: 'select', item: any): void;
    (e: 'clear'): void;
    (e: 'valid', isValid: boolean): void;
  }>();

  const inputRef = ref();
  const searchText = ref(props.modelValue);
  const focused = ref(false);
  const selectedIndex = ref(-1);

  // 监听输入值变化
  watch(
    () => props.modelValue,
    val => {
      searchText.value = val;
    },
  );

  watch(searchText, val => {
    emit('update:modelValue', val);
  });

  // 处理聚焦
  const handleFocus = () => {
    focused.value = true;
  };

  // 处理失焦
  const handleBlur = () => {
    setTimeout(() => {
      focused.value = false;
      selectedIndex.value = -1;
    }, 200);
  };

  // 处理清除
  const handleClear = () => {
    searchText.value = '';
    emit('clear');
  };

  // 处理搜索
  const handleSearch = () => {
    // 检查最小搜索长度
    if (props.minSearchLength > 0 && searchText.value.length < props.minSearchLength) {
      emit('valid', false);
      return;
    }

    // 如果有验证函数，执行验证
    if (props.validator) {
      const validation = props.validator(searchText.value);
      emit('valid', validation.valid);
      
      // 如果设置了只有验证通过才搜索，并且验证未通过，则不触发搜索
      if (props.searchOnValid && !validation.valid) {
        return;
      }
    }

    emit('search', searchText.value);
    focused.value = false;
  };

  // 处理选择建议
  const handleSelect = (item: any) => {
    searchText.value = typeof item === 'string' ? item : item.value;
    emit('select', item);
    focused.value = false;
  };

  // 对外暴露方法
  defineExpose({
    focus: () => inputRef.value?.focus(),
    blur: () => inputRef.value?.blur(),
    select: () => inputRef.value?.select(),
  });
</script>

<style>
  .search-input {
    position: relative;
    width: 100%;
  }

  .search-input__icon {
    color: var(--el-text-color-secondary);
  }

  .search-input__suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 4px;
    padding: var(--spacing-sm) 0;
    background-color: var(--el-bg-color);
    border: 1px solid var(--el-border-color-light);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
    overflow-y: auto;
    z-index: 10;
  }

  .search-input__suggestions-list {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .search-input__suggestion-item {
    padding: var(--spacing-sm) var(--spacing-md);
    cursor: pointer;
    transition: background-color var(--transition-duration);
  }

  .search-input__suggestion-item:hover,
  .search-input__suggestion-item.is-selected {
    background-color: var(--el-fill-color-light);
  }

  /* 暗色主题 */
  .dark .search-input__suggestions {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-darker);
    box-shadow: var(--box-shadow-dark);
  }
</style>
