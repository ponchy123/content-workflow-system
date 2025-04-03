import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const rootRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    meta: {
      title: '首页',
    },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/dashboard/dashboard.vue'),
        meta: { title: '棣栭〉', icon: 'home', public: true },
      },
    ],
  },
  {
    path: '/test',
    name: 'TestPage',
    component: () => import('@/views/TestPage.vue'),
    meta: { 
      title: '测试页面', 
      public: true, 
      requiresAuth: false 
    },
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面未找到', public: true },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '没有权限', public: true },
  },
  {
    path: '/500',
    name: 'ServerError',
    component: () => import('@/views/error/500.vue'),
    meta: { title: '服务器错误', public: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]; 