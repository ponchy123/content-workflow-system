import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const postalRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'postal',
        name: 'Postal',
        component: () => import('@/views/postal/index.vue'),
        meta: { title: '邮编管理', icon: 'location' },
      },
      {
        path: 'postal/zip-zones',
        name: 'ZipZones',
        component: () => import('@/views/postal/zip-zones.vue'),
        meta: { title: '邮编分区' },
      },
      {
        path: 'postal/remote-areas',
        name: 'RemoteAreas',
        component: () => import('@/views/postal/remote-areas.vue'),
        meta: { title: '偏远地区' },
      },
    ],
  },
]; 