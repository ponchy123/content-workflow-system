<template>
  <div
    v-if="loading"
    class="loading-spinner"
    :class="{
      'is-fullscreen': fullscreen,
      'is-transparent': transparent,
      [`loading-spinner--${size}`]: true,
    }"
  >
    <div class="loading-spinner__wrapper">
      <!-- 自定义图标 -->
      <slot name="icon">
        <div class="loading-spinner__icon">
          <svg viewBox="0 0 50 50" class="loading-spinner__circular">
            <circle cx="25" cy="25" r="20" fill="none" class="loading-spinner__path" />
          </svg>
        </div>
      </slot>

      <!-- 加载文本 -->
      <div v-if="text" class="loading-spinner__text">
        <slot name="text">{{ text }}</slot>
      </div>
    </div>

    <!-- 背景遮罩 -->
    <div v-if="background" class="loading-spinner__mask" :style="{ backgroundColor: background }" />
  </div>
</template>

<script setup lang="ts">
  interface Props {
    loading?: boolean;
    fullscreen?: boolean;
    transparent?: boolean;
    text?: string;
    background?: string;
    size?: 'small' | 'default' | 'large';
  }

  withDefaults(defineProps<Props>(), {
    loading: true,
    fullscreen: false,
    transparent: false,
    size: 'default',
    background: 'rgba(255, 255, 255, 0.9)',
  });
</script>

<style>
  .loading-spinner {
    position: relative;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 100px;
    min-height: 100px;
  }

  .loading-spinner.is-fullscreen {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 9999;
  }

  .loading-spinner__wrapper {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
  }

  .loading-spinner__icon {
    width: var(--loading-spinner-size, 32px);
    height: var(--loading-spinner-size, 32px);
    color: var(--el-color-primary);
    animation: loading-rotate 2s linear infinite;
  }

  .loading-spinner__circular {
    width: 100%;
    height: 100%;
    animation: loading-rotate 2s linear infinite;
  }

  .loading-spinner__path {
    stroke: currentColor;
    stroke-width: 3;
    stroke-linecap: round;
    animation: loading-dash 1.5s ease-in-out infinite;
  }

  .loading-spinner__text {
    font-size: var(--font-size-small);
    color: var(--el-text-color-regular);
  }

  .loading-spinner__mask {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    transition: background-color var(--transition-duration);
  }

  /* 尺寸变体 */
  .loading-spinner--small {
    --loading-spinner-size: 24px;
  }

  .loading-spinner--default {
    --loading-spinner-size: 32px;
  }

  .loading-spinner--large {
    --loading-spinner-size: 48px;
  }

  /* 透明背景 */
  .loading-spinner.is-transparent .loading-spinner__mask {
    background-color: transparent !important;
  }

  /* 动画 */
  @keyframes loading-rotate {
    100% {
      transform: rotate(360deg);
    }
  }

  @keyframes loading-dash {
    0% {
      stroke-dasharray: 1, 150;
      stroke-dashoffset: 0;
    }
    50% {
      stroke-dasharray: 90, 150;
      stroke-dashoffset: -35;
    }
    100% {
      stroke-dasharray: 90, 150;
      stroke-dashoffset: -124;
    }
  }

  /* 暗色主题 */
  .dark .loading-spinner__mask {
    background-color: rgba(0, 0, 0, 0.9);
  }
</style>
