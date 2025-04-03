<template>
  <div class="filter-panel" :class="{ 'is-collapsed': collapsed }">
    <!-- 面板头部 -->
    <div class="filter-panel__header">
      <div class="filter-panel__title">
        <slot name="title">{{ title }}</slot>
      </div>
      <div class="filter-panel__actions">
        <el-button
          v-if="collapsible"
          :icon="collapsed ? 'ArrowDown' : 'ArrowUp'"
          text
          @click="toggleCollapse"
        />
        <el-button v-if="clearable" text type="primary" @click="handleClear"> 清空筛选 </el-button>
      </div>
    </div>

    <!-- 面板内容 -->
    <div v-show="!collapsed" class="filter-panel__body">
      <el-form
        ref="formRef"
        :model="filterModel"
        :label-width="labelWidth"
        :label-position="labelPosition"
        :size="size"
      >
        <el-row :gutter="gutter">
          <el-col
            v-for="field in fields"
            :key="field.prop"
            :span="field.span || defaultSpan"
            :xs="field.xs"
            :sm="field.sm"
            :md="field.md"
            :lg="field.lg"
            :xl="field.xl"
          >
            <el-form-item :label="field.label" :prop="field.prop" :rules="field.rules">
              <!-- 输入框 -->
              <el-input
                v-if="field.type === 'input'"
                v-model="filterModel[field.prop]"
                v-bind="field.props"
                :placeholder="field.placeholder"
                @change="handleFieldChange(field.prop)"
              />

              <!-- 选择器 -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="filterModel[field.prop]"
                v-bind="field.props"
                :placeholder="field.placeholder"
                @change="handleFieldChange(field.prop)"
              >
                <el-option
                  v-for="option in field.options"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                  :disabled="option.disabled"
                />
              </el-select>

              <!-- 日期选择器 -->
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="filterModel[field.prop]"
                v-bind="field.props"
                :placeholder="field.placeholder"
                @change="handleFieldChange(field.prop)"
              />

              <!-- 日期范围选择器 -->
              <el-date-picker
                v-else-if="field.type === 'daterange'"
                v-model="filterModel[field.prop]"
                type="daterange"
                v-bind="field.props"
                :start-placeholder="field.startPlaceholder"
                :end-placeholder="field.endPlaceholder"
                @change="handleFieldChange(field.prop)"
              />

              <!-- 自定义组件 -->
              <component
                v-else-if="field.component"
                :is="field.component"
                v-model="filterModel[field.prop]"
                v-bind="field.props"
                @change="handleFieldChange(field.prop)"
              />

              <!-- 自定义插槽 -->
              <slot v-else :name="`field-${field.prop}`" :field="field" :model="filterModel" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 面板底部 -->
    <div v-if="$slots.footer" class="filter-panel__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, watch } from 'vue';
  import type { FormInstance } from 'element-plus';
  import type { FilterField } from './types';

  interface Props {
    fields: FilterField[];
    modelValue?: Record<string, any>;
    title?: string;
    labelWidth?: string | number;
    labelPosition?: 'right' | 'left' | 'top';
    size?: 'large' | 'default' | 'small';
    gutter?: number;
    defaultSpan?: number;
    collapsible?: boolean;
    clearable?: boolean;
  }

  const props = withDefaults(defineProps<Props>(), {
    fields: () => [],
    modelValue: () => ({}),
    labelWidth: 100,
    labelPosition: 'right',
    size: 'default',
    gutter: 20,
    defaultSpan: 6,
    collapsible: true,
    clearable: true,
  });

  const emit = defineEmits<{
    (e: 'update:modelValue', value: Record<string, any>): void;
    (e: 'change', field: string, value: any): void;
    (e: 'clear'): void;
  }>();

  const formRef = ref<FormInstance>();
  const collapsed = ref(false);
  const filterModel = reactive<Record<string, any>>({ ...props.modelValue });

  // 监听值变化
  watch(
    () => props.modelValue,
    val => {
      Object.assign(filterModel, val);
    },
    { deep: true },
  );

  watch(
    filterModel,
    val => {
      emit('update:modelValue', { ...val });
    },
    { deep: true },
  );

  // 切换折叠状态
  const toggleCollapse = () => {
    collapsed.value = !collapsed.value;
  };

  // 处理字段变化
  const handleFieldChange = (field: string) => {
    emit('change', field, filterModel[field]);
  };

  // 清空筛选
  const handleClear = () => {
    Object.keys(filterModel).forEach(key => {
      filterModel[key] = undefined;
    });
    emit('clear');
  };

  // 对外暴露方法
  defineExpose({
    validate: () => formRef.value?.validate(),
    resetFields: () => formRef.value?.resetFields(),
    clearValidate: (props?: string | string[]) => formRef.value?.clearValidate(props),
  });
</script>

<style>
  .filter-panel {
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
    margin-bottom: var(--spacing-large);
  }

  .filter-panel__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-base) var(--spacing-large);
    border-bottom: 1px solid var(--border-color-lighter);
  }

  .filter-panel__title {
    font-size: var(--font-size-medium);
    font-weight: var(--font-weight-bold);
    color: var(--text-color-primary);
  }

  .filter-panel__actions {
    display: flex;
    gap: var(--spacing-small);
  }

  .filter-panel__body {
    padding: var(--spacing-large);
  }

  .filter-panel__footer {
    padding: var(--spacing-base) var(--spacing-large);
    border-top: 1px solid var(--border-color-lighter);
    background-color: var(--fill-color-light);
  }

  /* 暗色主题 */
  .dark .filter-panel {
    background-color: var(--bg-color-overlay);
    box-shadow: var(--box-shadow-dark);
  }

  .dark .filter-panel__footer {
    background-color: var(--bg-color);
  }
</style>
