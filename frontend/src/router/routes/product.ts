import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const productRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'product',
        name: 'Product',
        component: () => import('@/views/product/index.vue'),
        meta: { title: '产品管理', icon: 'box' },
      },
      {
        path: 'product/list',
        name: 'ProductList',
        component: () => import('@/views/product/list.vue'),
        meta: { title: '产品列表' },
      },
      {
        path: 'product/detail/:id',
        name: 'ProductDetail',
        component: () => import('@/views/product/DetailWrapper.vue'),
        meta: { title: '产品详情' },
      },
      {
        path: 'product/edit/:id',
        name: 'ProductEdit',
        component: () => import('@/views/product/edit.vue'),
        meta: { title: '编辑产品' },
        props: route => {
          console.log('ProductEdit路由被访问,参数:', route.params, '查询参数:', route.query);
          return {
            id: route.params.id,
            tab: route.query.tab || 'basic'
          };
        },
      },
    ],
  },
]; 