<template>
  <div class="form-card">
    <!-- 卡片标题 -->
    <div v-if="title || $slots.title" class="form-card__header">
      <div class="form-card__title">
        <slot name="title">{{ title }}</slot>
      </div>
      <div v-if="$slots.actions" class="form-card__actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="form-card__body">
      <slot />
    </div>

    <!-- 卡片底部 -->
    <div v-if="$slots.footer" class="form-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
  interface Props {
    title?: string;
  }

  withDefaults(defineProps<Props>(), {
    title: '',
  });
</script>

<style>
  .form-card {
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
    margin-bottom: var(--spacing-lg);
  }

  .form-card__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  .form-card__title {
    font-size: var(--font-size-large);
    font-weight: var(--font-weight-bold);
    color: var(--el-text-color-primary);
    line-height: 1.5;
  }

  .form-card__actions {
    display: flex;
    gap: var(--spacing-sm);
  }

  .form-card__body {
    flex: 1;
    padding: var(--spacing-lg);
  }

  .form-card__footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--el-border-color-lighter);
    background-color: var(--el-fill-color-light);
    border-radius: 0 0 var(--border-radius-base) var(--border-radius-base);
  }

  /* 暗色主题 */
  .dark .form-card {
    background-color: var(--el-bg-color-overlay);
    box-shadow: var(--box-shadow-dark);
  }

  .dark .form-card__footer {
    background-color: var(--el-bg-color);
  }
</style>
