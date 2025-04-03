import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const fuelRateRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'fuel-rate',
        name: 'FuelRate',
        component: () => import('@/views/fuel-rate/index.vue'),
        meta: { title: '燃油费率', icon: 'oil' },
      },
    ],
  },
]; 