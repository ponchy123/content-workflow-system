<template>
  <div class="form-section">
    <el-form :model="settings" size="small" label-width="120px">
      <el-form-item label="最大通知数量">
        <el-input-number v-model="settings.maxCount" :min="10" :max="1000" :step="10" />
      </el-form-item>
      <el-form-item label="通知保留天数">
        <el-input-number v-model="settings.expirationDays" :min="1" :max="365" />
      </el-form-item>
      <el-form-item label="声音提醒">
        <el-switch v-model="settings.soundEnabled" />
      </el-form-item>
      <el-form-item label="桌面通知">
        <el-switch v-model="settings.desktopNotification" />
      </el-form-item>
      <el-form-item label="按模块分组">
        <el-switch v-model="settings.groupByModule" />
      </el-form-item>
      <el-form-item label="自动清理过期">
        <el-switch v-model="settings.autoCleanup" />
      </el-form-item>
    </el-form>
    <div class="dialog-footer">
      <el-button @click="handleReset">重置</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import type { NotificationSettings } from '@/types/notification';

  const props = defineProps<{
    modelValue: NotificationSettings;
  }>();

  const emit = defineEmits<{
    (e: 'update:modelValue', value: NotificationSettings): void;
    (e: 'reset'): void;
    (e: 'save'): void;
  }>();

  const settings = computed({
    get: () => props.modelValue,
    set: value => emit('update:modelValue', value),
  });

  const handleReset = () => {
    emit('reset');
  };

  const handleSave = () => {
    emit('save');
  };
</script>

<style scoped>
  .form-section {
    padding: var(--el-spacing-base);
    border-bottom: 1px solid var(--el-border-color-light);
  }

  .notification-settings {
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);

    .settings-header {
      padding: var(--spacing-base);
      border-bottom: 1px solid var(--border-color);

      .title {
        font-size: var(--font-size-large);
        font-weight: var(--font-weight-medium);
        color: var(--text-color-primary);
      }
    }

    .settings-body {
      padding: var(--spacing-large);

      .settings-section {
        margin-bottom: var(--spacing-large);

        .section-title {
          font-size: var(--font-size-medium);
          font-weight: var(--font-weight-medium);
          color: var(--text-color-primary);
          margin-bottom: var(--spacing-base);
        }

        .section-content {
          .setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--spacing-base) 0;
            border-bottom: 1px solid var(--border-color-light);

            &:last-child {
              border-bottom: none;
            }

            .item-label {
              color: var(--text-color-regular);

              .description {
                font-size: var(--font-size-small);
                color: var(--text-color-secondary);
                margin-top: var(--spacing-mini);
              }
            }
          }
        }
      }
    }

    .settings-footer {
      padding: var(--spacing-base);
      border-top: 1px solid var(--border-color);
      background-color: var(--bg-color-light);
      display: flex;
      justify-content: flex-end;
      gap: var(--spacing-base);
    }
  }
</style>
