<template>
  <el-tag :type="type" :effect="effect" :size="size" :class="['status-tag', `status-tag--${type}`]">
    <el-icon v-if="icon" class="status-tag__icon">
      <component :is="icon" />
    </el-icon>
    {{ text }}
  </el-tag>
</template>

<script setup lang="ts">
  interface Props {
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
    text: string;
    icon?: string;
    effect?: 'light' | 'dark' | 'plain';
    size?: 'large' | 'default' | 'small';
  }

  withDefaults(defineProps<Props>(), {
    type: 'info',
    effect: 'light',
    size: 'small',
  });
</script>

<style>
  .status-tag {
    /* 基础样式 */
    height: var(--status-tag-height, 24px);
    padding: var(--status-tag-padding, 0 var(--spacing-sm));
    font-size: var(--status-tag-font-size, var(--font-size-small));
    font-weight: var(--status-tag-font-weight, var(--font-weight-medium));
    border-radius: var(--status-tag-border-radius, var(--border-radius-base));
    display: inline-flex;
    align-items: center;
  }

  .status-tag__icon {
    margin-right: var(--status-tag-icon-margin, var(--spacing-xs));
    font-size: var(--status-tag-icon-size, 14px);
  }

  /* 状态样式 */
  .status-tag--processing {
    color: var(--status-tag-processing-color, var(--color-primary));
    background-color: var(--status-tag-processing-bg, var(--color-primary-light-9));
    border-color: var(--status-tag-processing-border, var(--color-primary-light-5));
  }

  .status-tag--pending {
    color: var(--status-tag-pending-color, var(--color-warning));
    background-color: var(--status-tag-pending-bg, var(--color-warning-light-9));
    border-color: var(--status-tag-pending-border, var(--color-warning-light-5));
  }

  .status-tag--completed {
    color: var(--status-tag-completed-color, var(--color-success));
    background-color: var(--status-tag-completed-bg, var(--color-success-light-9));
    border-color: var(--status-tag-completed-border, var(--color-success-light-5));
  }

  .status-tag--failed {
    color: var(--status-tag-failed-color, var(--color-danger));
    background-color: var(--status-tag-failed-bg, var(--color-danger-light-9));
    border-color: var(--status-tag-failed-border, var(--color-danger-light-5));
  }

  .status-tag--cancelled {
    color: var(--status-tag-cancelled-color, var(--color-info));
    background-color: var(--status-tag-cancelled-bg, var(--color-info-light-9));
    border-color: var(--status-tag-cancelled-border, var(--color-info-light-5));
  }
</style>
