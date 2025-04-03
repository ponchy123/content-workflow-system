<script setup lang="ts">
  import { computed } from 'vue';
  import { ElTag, ElButton, ElIcon } from 'element-plus';
  import { View, Delete } from '@element-plus/icons-vue';
  import { formatDistanceToNow } from 'date-fns';
  import { zhCN } from 'date-fns/locale';
  import type { Notification } from '@/types/notification';
  import { defineProps, defineEmits } from 'vue';
  import { formatNotificationTime } from '@/utils/notification';

  const props = defineProps<{
    notification: Notification;
  }>();

  const emit = defineEmits<{
    (e: 'view', notification: Notification): void;
    (e: 'delete', notification: Notification): void;
  }>();

  const typeColors = {
    success: 'success',
    warning: 'warning',
    info: 'info',
    error: 'danger',
  } as const;

  const timeAgo = computed(() =>
    formatDistanceToNow(new Date(props.notification.timestamp), {
      addSuffix: true,
      locale: zhCN,
    }),
  );

  const handleClick = () => {
    if (!props.notification.read) {
      emit('view', props.notification);
    }
  };

  const handleView = () => {
    emit('view', props.notification);
  };

  const handleDelete = () => {
    emit('delete', props.notification);
  };

  const getNotificationTypeTag = (type: string): 'success' | 'warning' | 'info' | 'danger' => {
    const typeMap = {
      success: 'success',
      warning: 'warning',
      info: 'info',
      error: 'danger',
    } as const;
    return typeMap[type as keyof typeof typeMap] || 'info';
  };

  const getNotificationTypeLabel = (type: string): string => {
    const typeMap = {
      success: '成功',
      warning: '警告',
      info: '信息',
      error: '错误',
    };
    return typeMap[type as keyof typeof typeMap] || type;
  };

  const getNotificationTypeColor = (type: string): string => {
    const colorMap = {
      success: '#67C23A',
      warning: '#E6A23C',
      info: '#909399',
      error: '#F56C6C'
    };
    return colorMap[type as keyof typeof colorMap] || colorMap.info;
  };
</script>

<template>
  <div
    class="notification-item"
    :class="{ 'notification-item--unread': !notification.read }"
    @click="handleClick"
  >
    <div class="notification-header">
      <ElTag
        :type="getNotificationTypeTag(notification.type)"
        :color="getNotificationTypeColor(notification.type)"
        size="small"
      >
        {{ getNotificationTypeLabel(notification.type) }}
      </ElTag>
      <span class="notification-time">{{ formatNotificationTime(notification.timestamp) }}</span>
    </div>

    <div class="notification-content">
      <h4 class="notification-title">{{ notification.title }}</h4>
      <p class="notification-message">{{ notification.message }}</p>
    </div>

    <div class="notification-footer">
      <div class="notification-module" v-if="notification.module">
        <ElTag size="small" effect="plain">{{ notification.module }}</ElTag>
      </div>
      <div class="notification-actions">
        <ElButton type="primary" link @click.stop="handleView">
          <ElIcon><View /></ElIcon>查看详情
        </ElButton>
        <ElButton type="danger" link @click.stop="handleDelete">
          <ElIcon><Delete /></ElIcon>删除
        </ElButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .notification-item {
    padding: var(--spacing-base);
    border-bottom: 1px solid var(--border-color-light);
    transition: background-color var(--transition-duration) var(--transition-function);
    cursor: pointer;
  }

  .notification-item:hover {
    background-color: var(--bg-color-light);
  }

  .notification-item:last-child {
    border-bottom: none;
  }

  .notification-item.notification-item--unread {
    background-color: var(--color-primary-light-9);
  }

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-small);
  }

  .notification-time {
    font-size: var(--font-size-small);
    color: var(--text-color-secondary);
  }

  .notification-content {
    color: var(--text-color-regular);
    margin-bottom: var(--spacing-small);
  }

  .notification-title {
    margin: 0 0 4px;
    font-size: var(--font-size-medium);
    font-weight: var(--font-weight-medium);
    color: var(--text-color-primary);
  }

  .notification-message {
    margin: 0;
    font-size: var(--font-size-small);
    color: var(--text-color-regular);
  }

  .notification-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .notification-module {
    .el-tag {
      background-color: var(--el-fill-color-light);
    }
  }

  .notification-actions {
    display: flex;
    gap: var(--spacing-small);
  }
</style>
