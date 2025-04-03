import type { RouteRecordRaw } from 'vue-router';

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/auth',
    component: () => import('@/layouts/auth.vue'),
    meta: { public: true },
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/login.vue'),
        meta: { title: '登录', public: true },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/register.vue'),
        meta: { title: '注册', public: true },
      },
      {
        path: 'forgot-password',
        name: 'ForgotPassword',
        component: () => import('@/views/auth/forgot-password.vue'),
        meta: { title: '忘记密码', public: true },
      },
      {
        path: 'reset-password/:uid/:token',
        name: 'ResetPassword',
        component: () => import('@/views/auth/reset-password.vue'),
        meta: { title: '重置密码', public: true },
      },
    ],
  },
]; 