<template>
  <div class="data-display" :class="{ 'is-vertical': vertical }">
    <!-- 标题 -->
    <div v-if="title || $slots.title" class="data-display__title">
      <slot name="title">{{ title }}</slot>
    </div>

    <!-- 数据项 -->
    <div class="data-display__items">
      <template v-for="(item, index) in items" :key="item.prop || index">
        <div
          class="data-display__item"
          :class="{
            'is-required': item.required,
            'is-error': item.error,
            [`data-display__item--${item.type || 'text'}`]: true,
          }"
          :style="{
            width: item.width || itemWidth,
            minWidth: item.minWidth,
            maxWidth: item.maxWidth,
          }"
        >
          <!-- 标签 -->
          <div class="data-display__label" :style="{ width: labelWidth }">
            <slot :name="`label-${item.prop}`">
              {{ item.label }}
              <span v-if="item.required" class="data-display__required">*</span>
            </slot>
          </div>

          <!-- 内容 -->
          <div class="data-display__content">
            <slot :name="`content-${item.prop}`" :value="getValue(item)">
              <template v-if="item.type === 'tag'">
                <el-tag :type="getTagType(item)" :effect="item.tagEffect" :size="item.tagSize">
                  {{ formatValue(getValue(item), item) }}
                </el-tag>
              </template>
              <template v-else-if="item.type === 'image'">
                <el-image
                  :src="getValue(item)"
                  :preview-src-list="[getValue(item)]"
                  :fit="item.imageFit"
                  :lazy="item.imageLazy"
                >
                  <template #error>
                    <div class="data-display__image-error">
                      <el-icon><picture-filled /></el-icon>
                    </div>
                  </template>
                </el-image>
              </template>
              <template v-else>
                {{ formatValue(getValue(item), item) }}
              </template>
            </slot>
          </div>

          <!-- 错误信息 -->
          <div v-if="item.error" class="data-display__error">
            {{ item.error }}
          </div>
        </div>
      </template>
    </div>

    <!-- 操作 -->
    <div v-if="$slots.actions" class="data-display__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { PictureFilled } from '@element-plus/icons-vue';

  interface DataItem {
    prop: string;
    label: string;
    type?: 'text' | 'tag' | 'image' | string;
    width?: string;
    minWidth?: string;
    maxWidth?: string;
    required?: boolean;
    error?: string;
    formatter?: (value: any) => string;
    tagType?: 'success' | 'warning' | 'info' | 'primary' | 'danger' | ((value: any) => 'success' | 'warning' | 'info' | 'primary' | 'danger');
    tagEffect?: 'light' | 'dark' | 'plain';
    tagSize?: 'large' | 'default' | 'small';
    imageFit?: 'fill' | 'contain' | 'cover' | 'none' | 'scale-down';
    imageLazy?: boolean;
  }

  interface Props {
    data: Record<string, any>;
    items: DataItem[];
    title?: string;
    vertical?: boolean;
    labelWidth?: string;
    itemWidth?: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    data: () => ({}),
    items: () => [],
    vertical: false,
    labelWidth: '100px',
    itemWidth: '50%',
  });

  // 获取值
  const getValue = (item: DataItem) => {
    return props.data[item.prop];
  };

  // 格式化值
  const formatValue = (value: any, item: DataItem) => {
    if (item.formatter) {
      return item.formatter(value);
    }
    return value;
  };

  // 获取标签类型
  const getTagType = (item: DataItem): 'success' | 'warning' | 'info' | 'primary' | 'danger' | undefined => {
    if (!item.tagType) return undefined;
    if (typeof item.tagType === 'function') {
      return item.tagType(getValue(item));
    }
    return item.tagType;
  };
</script>

<style>
  .data-display {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background-color: var(--el-bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
  }

  .data-display__title {
    font-size: var(--font-size-large);
    font-weight: var(--font-weight-bold);
    color: var(--el-text-color-primary);
    line-height: 1.5;
  }

  .data-display__items {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .data-display__item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .data-display__label {
    font-size: var(--font-size-base);
    color: var(--el-text-color-regular);
    line-height: 1.5;
  }

  .data-display__required {
    color: var(--el-color-danger);
    margin-left: 4px;
  }

  .data-display__content {
    font-size: var(--font-size-base);
    color: var(--el-text-color-primary);
    line-height: 1.5;
    word-break: break-all;
  }

  .data-display__error {
    font-size: var(--font-size-small);
    color: var(--el-color-danger);
    line-height: 1.5;
  }

  .data-display__actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--el-border-color-lighter);
  }

  /* 垂直布局 */
  .data-display.is-vertical {
    .data-display__items {
      flex-direction: column;
    }

    .data-display__item {
      width: 100% !important;
    }
  }

  /* 图片类型 */
  .data-display__item--image {
    .el-image {
      width: 100px;
      height: 100px;
      border-radius: var(--border-radius-base);
      overflow: hidden;
    }
  }

  .data-display__image-error {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    background-color: var(--el-fill-color-light);
    color: var(--el-text-color-secondary);
    font-size: 24px;
  }

  /* 暗色主题 */
  .dark .data-display {
    background-color: var(--el-bg-color-overlay);
    box-shadow: var(--box-shadow-dark);
  }
</style>
