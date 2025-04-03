import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';
import type { NotificationConfig } from '@/types/notification';

export const useNotificationConfig = defineStore('notificationConfig', {
  state: () => ({
    config: useStorage<NotificationConfig>('notificationConfig', {
      maxCount: 100,
      expirationDays: 30,
      soundEnabled: true,
      desktopNotification: true,
      groupByModule: true,
      autoCleanup: true,
    }),
  }),

  actions: {
    updateConfig(config: Partial<NotificationConfig>) {
      this.config = { ...this.config, ...config };
    },

    resetConfig() {
      this.config = {
        maxCount: 100,
        expirationDays: 30,
        soundEnabled: true,
        desktopNotification: true,
        groupByModule: true,
        autoCleanup: true,
      };
    },
  },
});
