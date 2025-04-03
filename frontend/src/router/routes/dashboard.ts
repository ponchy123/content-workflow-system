import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/dashboard.vue'),
        meta: { title: '仪表盘', requiresAuth: true },
      },
    ],
  },
]; 