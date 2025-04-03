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
    <el-date-picker
      ref="pickerRef"
      v-model="dateRange"
      v-bind="pickerProps"
      type="daterange"
      :start-placeholder="startPlaceholder"
      :end-placeholder="endPlaceholder"
      :disabled="disabled"
      :readonly="readonly"
      :clearable="clearable"
      :editable="editable"
      :size="size"
      :format="format"
      :value-format="valueFormat"
      :default-value="defaultValue"
      :default-time="defaultTime"
      :range-separator="rangeSeparator"
      :shortcuts="shortcuts"
      :disabled-date="disabledDate"
      :disabled-hours="disabledHours"
      :disabled-minutes="disabledMinutes"
      :disabled-seconds="disabledSeconds"
      @change="handleChange"
      @blur="handleBlur"
      @focus="handleFocus"
      @calendar-change="handleCalendarChange"
      @panel-change="handlePanelChange"
      @visible-change="handleVisibleChange"
    />
  </el-form-item>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import type { FormItemRule } from 'element-plus';

  interface Props {
    modelValue?: [Date | string | number, Date | string | number];
    prop?: string;
    label?: string;
    rules?: FormItemRule | FormItemRule[];
    required?: boolean;
    error?: string;
    showMessage?: boolean;
    inlineMessage?: boolean;
    size?: 'large' | 'default' | 'small';
    startPlaceholder?: string;
    endPlaceholder?: string;
    disabled?: boolean;
    readonly?: boolean;
    clearable?: boolean;
    editable?: boolean;
    format?: string;
    valueFormat?: string;
    defaultValue?: [Date, Date];
    defaultTime?: [Date, Date];
    rangeSeparator?: string;
    shortcuts?: { text: string; value: [Date, Date] }[];
    disabledDate?: (date: Date) => boolean;
    disabledHours?: () => number[];
    disabledMinutes?: (hour: number) => number[];
    disabledSeconds?: (hour: number, minute: number) => number[];
    pickerProps?: Record<string, any>;
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: () => ['', ''],
    startPlaceholder: '开始日期',
    endPlaceholder: '结束日期',
    clearable: true,
    editable: true,
    rangeSeparator: '至',
    pickerProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: [Date | string | number, Date | string | number]): void;
    (e: 'change', value: [Date | string | number, Date | string | number]): void;
    (e: 'blur', event: Event): void;
    (e: 'focus', event: Event): void;
    (e: 'calendar-change', dates: [Date, Date]): void;
    (e: 'panel-change', date: Date, mode: string, view: string): void;
    (e: 'visible-change', visible: boolean): void;
  }>();

  const pickerRef = ref();
  const dateRange = ref(props.modelValue);

  // 合并规则
  const mergedRules = computed(() => {
    if (!props.rules) return undefined;
    const rules = Array.isArray(props.rules) ? props.rules : [props.rules];
    if (props.required) {
      rules.unshift({ required: true, message: `请选择${props.label || ''}` });
    }
    return rules;
  });

  // 监听值变化
  watch(
    () => props.modelValue,
    val => {
      dateRange.value = val;
    },
  );

  watch(dateRange, val => {
    emit('update:modelValue', val);
  });

  // 事件处理
  const handleChange = (value: [Date | string | number, Date | string | number]) => {
    emit('change', value);
  };

  const handleBlur = (event: Event) => {
    emit('blur', event);
  };

  const handleFocus = (event: Event) => {
    emit('focus', event);
  };

  const handleCalendarChange = (dates: [Date, Date]) => {
    emit('calendar-change', dates);
  };

  const handlePanelChange = (date: Date, mode: string, view: string) => {
    emit('panel-change', date, mode, view);
  };

  const handleVisibleChange = (visible: boolean) => {
    emit('visible-change', visible);
  };

  // 对外暴露方法
  defineExpose({
    focus: () => pickerRef.value?.focus(),
  });
</script>

<style>
  .el-date-editor.el-input__wrapper {
    width: 100%;
  }

  /* 暗色主题 */
  .dark .el-date-editor.el-input__wrapper {
    --el-datepicker-border-color: var(--el-border-color-darker);
    --el-datepicker-off-text-color: var(--el-text-color-placeholder);
    --el-datepicker-header-text-color: var(--el-text-color-regular);
    --el-datepicker-icon-color: var(--el-text-color-regular);
    --el-datepicker-hover-text-color: var(--el-color-primary);
    --el-datepicker-active-color: var(--el-color-primary);
  }
</style>
