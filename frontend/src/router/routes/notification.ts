import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const notificationRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'notification',
        name: 'Notification',
        component: () => import('@/views/notification/index.vue'),
        meta: { title: '通知中心', icon: 'notification' },
      },
      {
        path: 'notification/settings',
        name: 'NotificationSettings',
        component: () => import('@/views/notification/settings.vue'),
        meta: { title: '通知设置' },
      },
    ],
  },
]; 