<template>
  <div class="error-boundary">
    <!-- 错误状态 -->
    <template v-if="error">
      <div class="error-boundary__content">
        <!-- 错误图标 -->
        <div class="error-boundary__icon">
          <slot name="icon">
            <el-icon :size="48" color="var(--el-color-danger)">
              <warning-filled />
            </el-icon>
          </slot>
        </div>

        <!-- 错误标题 -->
        <div class="error-boundary__title">
          <slot name="title" :error="error">
            {{ title || '组件渲染错误' }}
          </slot>
        </div>

        <!-- 错误描述 -->
        <div class="error-boundary__description">
          <slot name="description" :error="error">
            {{ description || error.message }}
          </slot>
        </div>

        <!-- 错误详情 -->
        <div v-if="showDetails" class="error-boundary__details">
          <el-collapse>
            <el-collapse-item title="错误详情">
              <pre class="error-boundary__stack">{{ error.stack }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 操作按钮 -->
        <div class="error-boundary__actions">
          <slot name="actions" :retry="handleRetry">
            <el-button type="primary" @click="handleRetry"> 重试 </el-button>
          </slot>
        </div>
      </div>
    </template>

    <!-- 正常内容 -->
    <template v-else>
      <slot />
    </template>
  </div>
</template>

<script setup lang="ts">
  import { ref, onErrorCaptured } from 'vue';
  import { WarningFilled } from '@element-plus/icons-vue';

  interface Props {
    title?: string;
    description?: string;
    showDetails?: boolean;
    onError?: (error: Error) => void;
    onRetry?: () => void;
  }

  const props = withDefaults(defineProps<Props>(), {
    showDetails: false,
  });

  const error = ref<Error | null>(null);

  // 捕获错误
  onErrorCaptured((err: Error) => {
    error.value = err;
    props.onError?.(err);
    return false; // 阻止错误继续传播
  });

  // 重试处理
  const handleRetry = () => {
    error.value = null;
    props.onRetry?.();
  };
</script>

<style>
  .error-boundary {
    width: 100%;
    height: 100%;
  }

  .error-boundary__content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-extra-large);
    text-align: center;
  }

  .error-boundary__icon {
    margin-bottom: var(--spacing-large);
  }

  .error-boundary__title {
    font-size: var(--font-size-large);
    font-weight: var(--font-weight-bold);
    color: var(--el-text-color-primary);
    margin-bottom: var(--spacing-base);
  }

  .error-boundary__description {
    font-size: var(--font-size-base);
    color: var(--el-text-color-regular);
    margin-bottom: var(--spacing-large);
  }

  .error-boundary__details {
    width: 100%;
    max-width: 800px;
    margin-bottom: var(--spacing-large);
  }

  .error-boundary__stack {
    font-family: monospace;
    font-size: var(--font-size-small);
    color: var(--el-text-color-secondary);
    white-space: pre-wrap;
    text-align: left;
    padding: var(--spacing-base);
    background-color: var(--el-fill-color-light);
    border-radius: var(--border-radius-base);
  }

  .error-boundary__actions {
    display: flex;
    gap: var(--spacing-base);
  }

  /* 暗色主题 */
  .dark .error-boundary__stack {
    background-color: var(--el-bg-color-overlay);
  }
</style>
