<template>
  <el-badge
    :value="value"
    :max="max"
    :is-dot="isDot"
    :hidden="hidden"
    :type="type"
    class="status-badge"
    :class="[`status-badge--${type}`, { 'is-dot': isDot }]"
  >
    <slot />
  </el-badge>
</template>

<script setup lang="ts">
  interface Props {
    value?: string | number;
    max?: number;
    isDot?: boolean;
    hidden?: boolean;
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  }

  withDefaults(defineProps<Props>(), {
    type: 'info',
    isDot: false,
    hidden: false,
  });
</script>

<style>
  .status-badge {
    display: inline-flex;
  }

  .status-badge.is-dot .el-badge__content {
    width: var(--status-badge-dot-size, 8px);
    height: var(--status-badge-dot-size, 8px);
    padding: 0;
    right: var(--status-badge-dot-right, 5px);
    top: var(--status-badge-dot-top, 5px);
  }

  /* 状态样式 */
  .status-badge--primary .el-badge__content {
    background-color: var(--el-color-primary);
  }

  .status-badge--success .el-badge__content {
    background-color: var(--el-color-success);
  }

  .status-badge--warning .el-badge__content {
    background-color: var(--el-color-warning);
  }

  .status-badge--danger .el-badge__content {
    background-color: var(--el-color-danger);
  }

  .status-badge--info .el-badge__content {
    background-color: var(--el-color-info);
  }

  /* 暗色主题 */
  .dark .status-badge .el-badge__content {
    border: 1px solid var(--el-border-color-darker);
  }
</style>
