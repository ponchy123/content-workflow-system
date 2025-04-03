import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const reportRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/report/index.vue'),
        meta: { title: '报表分析', icon: 'chart' },
      },
      {
        path: 'report/usage',
        name: 'ReportUsage',
        component: () => import('@/views/report/usage.vue'),
        meta: { title: '使用统计' },
      },
      {
        path: 'report/cost',
        name: 'ReportCost',
        component: () => import('@/views/report/cost.vue'),
        meta: { title: '成本分析' },
      },
      {
        path: 'report/export',
        name: 'ReportExport',
        component: () => import('@/views/report/export.vue'),
        meta: { title: '数据导出' },
      },
    ],
  },
]; 