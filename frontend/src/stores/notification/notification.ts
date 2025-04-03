import { defineStore } from 'pinia';
import { computed, watch } from 'vue';
import { useStorage } from '@vueuse/core';
import type {
  Notification,
  NotificationConfig,
  NotificationType,
  NotificationSoundConfig,
} from '@/types/notification';
import {
  getNotificationList,
  type NotificationListParams,
  type NotificationListResponse,
  type NotificationUpdateParams,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification as apiDeleteNotification,
  clearReadNotifications,
  updateNotification,
} from '@/api/notifications/notifications';
import { useNotificationFilter } from './filter';
import { useNotificationConfig } from './config';
import { notificationManager } from '@/utils/notification';

export const useNotificationStore = defineStore('notification', () => {
  // 持久化存储
  const notifications = useStorage<Notification[]>('notifications', []);
  const isLoading = useStorage('notification_loading', false);
  const error = useStorage<string | null>('notification_error', null);
  const total = useStorage('notification_total', 0);
  const wsConnected = useStorage('notification_ws_connected', false);
  const lastSyncTime = useStorage<number>('lastNotificationSync', 0);
  const settings = useStorage<NotificationConfig>('notification_settings', {
    maxCount: 50,
    expirationDays: 7,
    soundEnabled: true,
    desktopNotification: true,
    groupByModule: true,
    autoCleanup: true,
  });

  // 声明声音配置
  const soundConfig: NotificationSoundConfig = {
    success: '/sounds/success.mp3',
    warning: '/sounds/warning.mp3',
    error: '/sounds/error.mp3',
    info: '/sounds/info.mp3',
    system: '/sounds/system.mp3',
    business: '/sounds/business.mp3',
  };

  // 自动清理过期通知
  watch(
    () => notifications.value.length,
    () => {
      const configStore = useNotificationConfig();
      if (configStore.config.autoCleanup) {
        cleanupExpiredNotifications();
      }
    },
  );

  // Computed
  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length);

  const availableModules = computed(() => [
    ...new Set(notifications.value.map(n => n.module).filter(Boolean)),
  ]);

  const availableTypes = computed(() => [...new Set(notifications.value.map(n => n.type))]);

  const todayCount = computed(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return notifications.value.filter(n => new Date(n.timestamp) >= today).length;
  });

  const weekCount = computed(() => {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    weekAgo.setHours(0, 0, 0, 0);
    return notifications.value.filter(n => new Date(n.timestamp) >= weekAgo).length;
  });

  const typeBreakdown = computed(() => {
    const breakdown: Record<string, number> = {};
    notifications.value.forEach(n => {
      breakdown[n.type] = (breakdown[n.type] || 0) + 1;
    });
    return breakdown;
  });

  const filteredNotifications = computed(() => {
    const filterStore = useNotificationFilter();
    const filter = filterStore.filter;

    return notifications.value.filter(notification => {
      if (
        filter.search &&
        !notification.title.toLowerCase().includes(filter.search.toLowerCase()) &&
        !notification.message.toLowerCase().includes(filter.search.toLowerCase())
      ) {
        return false;
      }

      if (filter.module && notification.module !== filter.module) {
        return false;
      }

      if (filter.type && notification.type !== filter.type) {
        return false;
      }

      if (filter.read !== null && notification.read !== filter.read) {
        return false;
      }

      if (filter.startDate && new Date(notification.timestamp) < filter.startDate) {
        return false;
      }
      if (filter.endDate && new Date(notification.timestamp) > filter.endDate) {
        return false;
      }

      return true;
    });
  });

  const groupedNotifications = computed(() => {
    const configStore = useNotificationConfig();
    if (!configStore.config.groupByModule) {
      return { default: filteredNotifications.value };
    }

    return filteredNotifications.value.reduce(
      (groups, notification) => {
        const module = notification.module || 'default';
        if (!groups[module]) {
          groups[module] = [];
        }
        groups[module].push(notification);
        return groups;
      },
      {} as Record<string, Notification[]>,
    );
  });

  // Actions
  async function fetchNotifications(params?: NotificationListParams) {
    try {
      isLoading.value = true;
      error.value = null;
      const response = await getNotificationList(params);

      // 合并本地和远程通知
      const remoteNotifications = response.items;
      const localNotifications = notifications.value;

      // 使用 Map 来去重和更新
      const notificationMap = new Map<string, Notification>();
      const allNotifications = [...localNotifications, ...remoteNotifications] as Notification[];
      allNotifications.forEach(notification => {
        notificationMap.set(notification.id, notification);
      });

      notifications.value = Array.from(notificationMap.values());
      total.value = response.total;
      lastSyncTime.value = Date.now();
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取通知失败';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function markAsRead(id: string) {
    try {
      await markNotificationAsRead(id);
      const notification = notifications.value.find(n => n.id === id);
      if (notification && !notification.read) {
        notification.read = true;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '标记已读失败';
      throw err;
    }
  }

  async function markAllAsRead() {
    try {
      await markAllNotificationsAsRead();
      notifications.value.forEach(n => {
        if (!n.read) {
          n.read = true;
        }
      });
    } catch (err) {
      error.value = err instanceof Error ? err.message : '标记全部已读失败';
      throw err;
    }
  }

  async function deleteNotification(id: string) {
    try {
      await apiDeleteNotification(id);
      const index = notifications.value.findIndex(n => n.id === id);
      if (index > -1) {
        const notification = notifications.value[index];
        notifications.value.splice(index, 1);
        total.value--;
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除通知失败';
      throw err;
    }
  }

  async function clearAllNotifications() {
    try {
      await clearReadNotifications();
      notifications.value = notifications.value.filter(n => !n.read);
      total.value = notifications.value.length;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清除已读通知失败';
      throw err;
    }
  }

  function cleanupExpiredNotifications() {
    const configStore = useNotificationConfig();
    const expirationDays = configStore.config.expirationDays;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - expirationDays);

    notifications.value = notifications.value.filter(
      notification => new Date(notification.timestamp) > cutoffDate,
    );
  }

  async function handleNewNotification(notification: Notification) {
    const configStore = useNotificationConfig();

    // 处理通知提醒
    await notificationManager.handleNewNotification(notification);

    // 添加到列表
    notifications.value.unshift(notification);

    // 控制通知数量
    if (notifications.value.length > configStore.config.maxCount) {
      notifications.value = notifications.value.slice(0, configStore.config.maxCount);
    }

    if (!notification.read) {
      if (settings.value.soundEnabled) {
        await notificationManager.playSound(soundConfig[notification.type]);
      }
      if (settings.value.desktopNotification) {
        await notificationManager.showDesktopNotification(notification);
      }
    }

    total.value++;
  }

  function setWebSocketConnected(connected: boolean) {
    wsConnected.value = connected;
  }

  // 定期同步通知
  async function syncNotifications() {
    const now = Date.now();
    // 如果距离上次同步超过5分钟，则重新同步
    if (now - lastSyncTime.value > 5 * 60 * 1000) {
      await fetchNotifications();
    }
  }

  // 设置相关
  async function fetchSettings() {
    try {
      const response = await getNotificationList({
        page: 1,
        page_size: 1,
        type: 'system' as NotificationType,
      });
      if (response.items.length > 0) {
        const settingsData = response.items[0];
        settings.value = {
          maxCount: settingsData.data?.maxCount ?? 50,
          expirationDays: settingsData.data?.expirationDays ?? 7,
          soundEnabled: settingsData.data?.soundEnabled ?? true,
          desktopNotification: settingsData.data?.desktopNotification ?? true,
          groupByModule: settingsData.data?.groupByModule ?? true,
          autoCleanup: settingsData.data?.autoCleanup ?? true,
        };
      }
      return settings.value;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设置失败';
      throw err;
    }
  }

  async function updateSettings(newSettings: Partial<NotificationConfig>) {
    try {
      await updateNotification('settings', {
        type: 'system' as NotificationType,
        content: JSON.stringify(newSettings),
        metadata: newSettings,
      });
      settings.value = { ...settings.value, ...newSettings };
      return settings.value;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新设置失败';
      throw err;
    }
  }

  async function updateNotificationSettings(id: string, data: NotificationUpdateParams) {
    try {
      await updateNotification(id, data);
      const notification = notifications.value.find(n => n.id === id);
      if (notification) {
        Object.assign(notification, data);
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新通知失败';
      throw err;
    }
  }

  return {
    // State
    notifications,
    isLoading,
    error,
    total,
    wsConnected,
    lastSyncTime,
    settings,

    // Computed
    unreadCount,
    availableModules,
    availableTypes,
    filteredNotifications,
    groupedNotifications,
    todayCount,
    weekCount,
    typeBreakdown,

    // Actions
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAllNotifications,
    cleanupExpiredNotifications,
    handleNewNotification,
    setWebSocketConnected,
    syncNotifications,
    fetchSettings,
    updateSettings,
    updateNotificationSettings,
  };
});
