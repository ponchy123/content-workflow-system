<template>
  <div class="unit-input" :class="{ 'show-unit-select': showUnitSelect }">
    <el-input-number
      v-if="type === 'number'"
      ref="inputRef"
      v-model="numberValue"
      v-bind="inputProps"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :controls="false"
      class="custom-controls"
      @blur="handleBlur"
      @focus="handleFocus"
      @change="handleNumberChange"
    >
      <template #decrease>
        <div class="number-button decrease">-</div>
      </template>
      <template #increase>
        <div class="number-button increase">+</div>
      </template>
    </el-input-number>
    <el-input
      v-else
      ref="inputRef"
      v-model="inputValue"
      v-bind="inputProps"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :clearable="clearable"
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
    </el-input>
    
    <el-select
      v-if="showUnitSelect && units.length"
      v-model="selectedUnit"
      :disabled="disabled"
      :size="size"
      class="unit-select"
      @change="handleUnitChange"
    >
      <el-option
        v-for="unit in units"
        :key="unit.value"
        :label="unit.label"
        :value="unit.value"
      />
    </el-select>
    <div v-else-if="units.length" class="unit-display">
      {{ selectedUnit }}
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import type { FormItemRule } from 'element-plus';

  interface Unit {
    label: string;
    value: string;
  }

  interface Props {
    modelValue?: string | number;
    unit?: string;
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
    maxlength?: number;
    minlength?: number;
    showWordLimit?: boolean;
    validateEvent?: boolean;
    units?: Unit[];
    defaultUnit?: string;
    inputProps?: Record<string, any>;
    showUnitSelect?: boolean;
    controls?: boolean;
    name?: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: '',
    type: 'number',
    showMessage: true,
    inlineMessage: false,
    size: 'default',
    clearable: false,
    showWordLimit: false,
    validateEvent: true,
    units: () => [],
    inputProps: () => ({}),
    showUnitSelect: false,
    controls: true,
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string | number): void;
    (e: 'update:unit', unit: string): void;
    (e: 'unit-change', unit: string): void;
    (e: 'blur', event: Event): void;
    (e: 'focus', event: Event): void;
    (e: 'change', value: { value: string | number; unit: string, target?: { name: string } }): void;
    (e: 'input', value: string | number): void;
    (e: 'clear'): void;
  }>();

  const inputRef = ref();
  const inputValue = ref<string>('');
  const numberValue = ref<number | undefined>(undefined);
  const selectedUnit = ref(props.unit || props.defaultUnit || props.units[0]?.value || '');

  // 设置初始值
  if (typeof props.modelValue === 'number') {
    numberValue.value = props.modelValue;
  } else if (typeof props.modelValue === 'string') {
    inputValue.value = props.modelValue;
  }

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
      if (typeof val === 'number') {
        numberValue.value = val;
      } else if (typeof val === 'string') {
        inputValue.value = val;
      }
    },
  );

  watch(
    () => props.unit,
    val => {
      if (val) {
        selectedUnit.value = val;
      }
    },
  );

  watch(inputValue, val => {
    emit('update:modelValue', val);
  });

  watch(numberValue, val => {
    if (val !== undefined) {
      emit('update:modelValue', val);
    }
  });

  watch(selectedUnit, val => {
    emit('update:unit', val);
  });

  // 事件处理
  const handleBlur = (event: Event) => {
    emit('blur', event);
  };

  const handleFocus = (event: Event) => {
    emit('focus', event);
  };

  const handleChange = (value: string) => {
    emit('change', { 
      value, 
      unit: selectedUnit.value,
      target: props.name ? { name: props.name } : undefined
    });
  };

  const handleNumberChange = (value: number | undefined) => {
    if (value !== undefined) {
      emit('change', { 
        value, 
        unit: selectedUnit.value,
        target: props.name ? { name: props.name } : undefined
      });
    }
  };

  const handleInput = (value: string) => {
    emit('input', value);
  };

  const handleClear = () => {
    emit('clear');
  };

  const handleUnitChange = (unit: string) => {
    selectedUnit.value = unit;
    emit('unit-change', unit);
    emit('update:unit', unit);
    
    const currentValue = props.type === 'number' 
      ? numberValue.value 
      : inputValue.value;
      
    if (currentValue !== undefined) {
      emit('change', { 
        value: currentValue, 
        unit,
        target: props.name ? { name: props.name } : undefined
      });
    }
  };

  // 对外暴露方法
  defineExpose({
    focus: () => inputRef.value?.focus(),
    blur: () => inputRef.value?.blur(),
    select: () => inputRef.value?.select(),
  });
</script>

<style scoped>
  /* 设置CSS变量 */
  :root {
    --form-control-height: 32px;
    --unit-input-select-width: 50px; /* 减小单位选择器宽度 */
    --unit-input-gap: 2px; /* 进一步减少间距 */
  }

  /* 基础样式 */
  .unit-input {
    display: flex;
    align-items: center;
    gap: var(--unit-input-gap); /* 使用更小的间距 */
    width: 100%;
  }

  /* 输入框样式 */
  .unit-input :deep(.el-input-number),
  .unit-input :deep(.el-input) {
    flex: 1;
  }

  /* 自定义数字输入控件样式 */
  .unit-input :deep(.el-input-number.custom-controls .el-input-number__decrease),
  .unit-input :deep(.el-input-number.custom-controls .el-input-number__increase) {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--el-fill-color-light);
    color: var(--el-text-color-regular);
    font-size: 13px;
    text-align: center;
    padding: 0 4px;
  }

  /* 单位显示样式 */
  .unit-input .unit-display {
    padding: 0 4px; /* 减少内边距 */
    height: var(--form-control-height);
    line-height: var(--form-control-height);
    border: 1px solid var(--el-border-color);
    background-color: var(--el-fill-color-light);
    color: var(--el-text-color-regular);
    white-space: nowrap;
    font-size: 13px;
    border-radius: var(--el-border-radius-base);
    width: var(--unit-input-select-width);
    text-align: center;
    margin-left: 0; /* 移除左边距 */
  }

  /* 单位选择器样式优化 */
  .unit-input .unit-select {
    width: var(--unit-input-select-width);
    margin-left: 0; /* 移除左边距 */
  }
  
  .unit-input .unit-select :deep(.el-input__wrapper) {
    padding: 0 4px; /* 减少内边距 */
    background-color: var(--el-fill-color-light);
    border-radius: var(--el-border-radius-base);
    height: var(--form-control-height);
    box-sizing: border-box;
  }

  .unit-input .unit-select :deep(.el-select__caret) {
    color: var(--el-text-color-secondary);
    font-size: 12px;
    right: 2px; /* 调整下拉箭头位置 */
  }
  
  .unit-input .unit-select :deep(.el-input__inner) {
    color: var(--el-text-color-regular);
    font-size: 13px;
    text-align: center;
    padding: 0 2px; /* 减少内边距 */
  }

  /* 暗色主题 */
  .dark .unit-input .unit-display,
  .dark .unit-input .unit-select :deep(.el-input__wrapper) {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-darker);
  }
</style>
