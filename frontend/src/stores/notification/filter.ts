import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';
import type { NotificationFilter } from '@/types/notification';

export const useNotificationFilter = defineStore('notificationFilter', {
  state: () => ({
    filter: useStorage<NotificationFilter>('notificationFilter', {
      search: '',
      module: null,
      type: null,
      read: null,
      startDate: null,
      endDate: null,
    }),
  }),

  actions: {
    setFilter(filter: Partial<NotificationFilter>) {
      this.filter = { ...this.filter, ...filter };
    },

    resetFilter() {
      this.filter = {
        search: '',
        module: null,
        type: null,
        read: null,
        startDate: null,
        endDate: null,
      };
    },
  },
});
