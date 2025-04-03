<template>
  <div class="base-rate-editor">
    <div class="editor-header">
      <div class="title">
        <slot name="title">{{ title }}</slot>
      </div>
      <div class="actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <div class="editor-body">
      <div class="rate-form">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  defineProps({
    title: {
      type: String,
      default: '',
    },
  });
</script>

<style>
  .base-rate-editor {
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
  }

  .base-rate-editor .editor-header {
    padding: var(--spacing-base);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .base-rate-editor .editor-header .title {
    font-size: var(--font-size-medium);
    font-weight: var(--font-weight-medium);
    color: var(--text-color-primary);
  }

  .base-rate-editor .editor-header .actions {
    display: flex;
    gap: var(--spacing-small);
  }

  .base-rate-editor .editor-body {
    padding: var(--spacing-large);
  }

  .base-rate-editor .rate-form {
    max-width: 800px;
    margin: 0 auto;
  }

  .base-rate-editor :deep(.form-section) {
    margin-bottom: var(--spacing-extra-large);
  }

  .base-rate-editor :deep(.section-title) {
    font-size: var(--font-size-medium);
    font-weight: var(--font-weight-medium);
    color: var(--text-color-primary);
    margin-bottom: var(--spacing-base);
    padding-bottom: var(--spacing-small);
    border-bottom: 1px solid var(--border-color-light);
  }

  .base-rate-editor :deep(.el-form-item) {
    margin-bottom: var(--spacing-large);
  }

  .base-rate-editor :deep(.el-form-item__label) {
    font-weight: var(--font-weight-medium);
    color: var(--text-color-regular);
  }

  .base-rate-editor :deep(.el-form-item__content .el-input-number),
  .base-rate-editor :deep(.el-form-item__content .el-select),
  .base-rate-editor :deep(.el-form-item__content .el-cascader),
  .base-rate-editor :deep(.el-form-item__content .el-date-editor) {
    width: 100%;
  }

  .base-rate-editor :deep(.form-tip) {
    font-size: var(--font-size-small);
    color: var(--text-color-secondary);
    margin-top: var(--spacing-mini);
  }
</style>
