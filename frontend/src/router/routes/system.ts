import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const systemRoutes: RouteRecordRaw[] = [
  {
    path: '/system',
    name: 'System',
    component: Layout,
    redirect: '/system/provider',
    meta: {
      title: '系统管理',
      icon: 'setting',
      order: 900
    },
    children: [
      {
        path: 'provider',
        name: 'ServiceProvider',
        component: () => import('@/views/system/provider/index.vue'),
        meta: {
          title: '服务商管理',
          icon: 'provider',
          order: 901
        }
      },
      {
        path: 'config',
        name: 'SystemConfig',
        component: () => import('@/views/system/config/index.vue'),
        meta: {
          title: '系统配置',
          icon: 'config',
          order: 902
        }
      }
    ]
  }
]; 