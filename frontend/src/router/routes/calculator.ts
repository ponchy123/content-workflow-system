import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const calculatorRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'calculator',
        name: 'Calculator',
        component: () => import('@/views/calculator/index.vue'),
        meta: { title: '运费计算', icon: 'calculator' },
      },
      {
        path: 'calculator/single',
        name: 'SingleCalc',
        component: () => import('@/views/calculator/single.vue'),
        meta: { title: '单票计算' },
      },
      {
        path: 'calculator/batch',
        name: 'BatchCalc',
        component: () => import('@/views/calculator/batch.vue'),
        meta: { title: '批量计算' },
      },
      {
        path: 'calculator/compare',
        name: 'Compare',
        component: () => import('@/views/calculator/compare.vue'),
        meta: { title: '产品比较' },
      },
      {
        path: 'calculator/history',
        name: 'History',
        component: () => import('@/views/calculator/history.vue'),
        meta: { title: '计算历史' },
      },
      {
        path: 'calculator/history/:id',
        name: 'HistoryDetail',
        component: () => import('@/views/calculator/history-detail.vue'),
        meta: { title: '历史详情' },
      },
    ],
  },
]; 