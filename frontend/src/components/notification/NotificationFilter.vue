<template>
  <filter-panel
    :fields="filterFields"
    :initial-values="modelValue"
    :loading="loading"
    title="通知过滤"
    @search="handleApply"
    @reset="handleReset"
  />
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { FilterPanel } from '@/components/common';
  import type { FilterField } from '@/components/common/data/types';
  import { useNotificationStore } from '@/stores/notification/notification';
  import type { NotificationFilter } from '@/types/notification';

  const props = defineProps<{
    modelValue: NotificationFilter;
    loading?: boolean;
  }>();

  const emit = defineEmits<{
    (e: 'update:modelValue', value: NotificationFilter): void;
    (e: 'reset'): void;
    (e: 'apply'): void;
  }>();

  const notificationStore = useNotificationStore();

  const filterFields = computed<FilterField[]>(() => [
    {
      type: 'input',
      label: '搜索',
      prop: 'search',
      placeholder: '搜索通知...',
    },
    {
      type: 'select',
      label: '模块',
      prop: 'module',
      placeholder: '选择模块',
      options: notificationStore.availableModules
        .filter((module): module is string => typeof module === 'string')
        .map(module => ({
          label: module,
          value: module,
          disabled: false
        })),
    },
    {
      type: 'select',
      label: '类型',
      prop: 'type',
      placeholder: '选择类型',
      options: notificationStore.availableTypes
        .filter((type): type is string => typeof type === 'string')
        .map(type => ({
          label: getNotificationTypeLabel(type),
          value: type,
          disabled: false
        })),
    },
    {
      type: 'select',
      label: '状态',
      prop: 'read',
      placeholder: '选择状态',
      options: [
        { label: '未读', value: false, disabled: false },
        { label: '已读', value: true, disabled: false },
      ],
    },
    {
      type: 'daterange',
      label: '日期范围',
      prop: 'dateRange',
      startPlaceholder: '开始日期',
      endPlaceholder: '结束日期',
      props: {
        valueFormat: 'YYYY-MM-DD'
      }
    },
  ]);

  const getNotificationTypeLabel = (type: string): string => {
    const typeMap = {
      success: '成功',
      warning: '警告',
      info: '信息',
      error: '错误',
    };
    return typeMap[type as keyof typeof typeMap] || type;
  };

  const handleReset = () => {
    emit('reset');
  };

  const handleApply = (values: NotificationFilter) => {
    emit('update:modelValue', values);
    emit('apply');
  };
</script>

<style scoped>
  .form-section {
    padding: var(--el-spacing-base);
    border-bottom: 1px solid var(--el-border-color-light);
  }
</style>
